"""Extract the 526 foods in VTN_FCT_2007.pdf into the project's CSV schema.

Nutrients are per 100 g edible portion. PDF '-' means unavailable; by default
it is imputed as zero for compatibility and recorded in a separate report.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import re
import unicodedata

import pdfplumber

ROOT = Path(__file__).resolve().parent
COLUMNS = ["STT", "Tên Thực Phẩm", "Fat (g)", "Carbs (g)", "Protein (g)",
           "Calories (kcal)", "Nhóm thực phẩm", "Nhóm Đa lượng chính"]
GROUPS = [(23, "Ngũ cốc và sản phẩm chế biến"),
          (49, "Khoai củ và sản phẩm chế biến"),
          (82, "Hạt, quả giàu đạm, béo và sản phẩm chế biến"),
          (208, "Rau, quả, củ dùng làm rau"), (264, "Quả chín"),
          (278, "Dầu, mỡ, bơ"), (360, "Thịt và sản phẩm chế biến"),
          (419, "Thủy sản và sản phẩm chế biến"),
          (430, "Trứng và sản phẩm chế biến"), (439, "Sữa và sản phẩm chế biến"),
          (460, "Đồ hộp"), (487, "Đồ ngọt (đường, bánh, mứt, kẹo)"),
          (510, "Gia vị, nước chấm"), (526, "Nước giải khát, bia, rượu")]
# TCVN3 (ABC) is used only in the Vietnamese name field of this edition.
LEGACY = "µ¸¶·¹¨»¾¼½Æ©ÇÊÈÉË®ÌÐÎÏÑªÒÕÓÔÖ×ÝØÜÞßãáâä«åèæçé¬êíëìîïóñòô\u00adõøö÷ùúýûüþ¡¢§£¤¥¦"
UNICODE = "àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵĂÂĐÊÔƠƯ"
TCVN3 = str.maketrans(LEGACY, UNICODE)
TCVN3.update(str.maketrans({"μ": "à", "−": "ư"}))
PATTERNS = {"Fat (g)": r"^Lipid\s*\(Fat\)\s+g\s+(\S+)",
            "Carbs (g)": r"^Glucid\s*\(Carbohydrate\)\s+g\s+(\S+)",
            "Protein (g)": r"^Protein\s+g\s+(\S+)",
            "Calories (kcal)": r"^.*?\(Energy\)\s+KCal\s+(\S+)"}


def classify(fat, carbs, protein):
    """Largest energy contribution; protein wins ties, as in existing CSV."""
    scores = {"Protein-rich": protein * 4, "Carb-rich": carbs * 4, "Fat-rich": fat * 9}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "Không xác định"


def extract_record(text, page_number, missing_policy, issues):
    header = re.search(r"\(\s*Vietnamese\s*\)\s*:?\s*(.*?)\s+STT:\s*(\d+)", text, re.S)
    if not header:
        return None
    number = int(header.group(2))
    if not 1 <= number <= 526:
        raise ValueError(f"Page {page_number}: invalid STT {number}")
    name = unicodedata.normalize("NFC", " ".join(header.group(1).translate(TCVN3).split()))
    if not name or "(cid:" in name:
        raise ValueError(f"Page {page_number}: unreadable food name")
    name = name[0].upper() + name[1:]
    values = {}
    for column, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.M | re.I)
        if not match:
            raise ValueError(f"Page {page_number}, STT {number}: cannot extract {column}")
        token = match.group(1)
        if token in {"-", "–", "—"}:
            if missing_policy == "error":
                raise ValueError(f"Page {page_number}, STT {number}: missing {column}")
            issues.append({"page": page_number, "STT": number, "column": column,
                           "source": token, "action": "imputed_zero"})
            value = 0.0
        else:
            value = float(token.replace(",", "."))
        if not math.isfinite(value) or value < 0 or (column != "Calories (kcal)" and value > 100):
            raise ValueError(f"Page {page_number}, STT {number}: invalid {column}: {token}")
        values[column] = value
    return {"STT": number, "Tên Thực Phẩm": name, **values,
            "Nhóm thực phẩm": next(group for end, group in GROUPS if number <= end),
            "Nhóm Đa lượng chính": classify(values["Fat (g)"], values["Carbs (g)"], values["Protein (g)"])}


def convert(input_path, output_path, missing_policy="zero"):
    records, issues = {}, []
    with pdfplumber.open(input_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            record = extract_record(page.extract_text() or "", page_number, missing_policy, issues)
            if record:
                number = record["STT"]
                if number in records:
                    raise ValueError(f"Duplicate STT {number} on page {page_number}")
                records[number] = record
            page.close()
            if page_number % 50 == 0:
                print(f"Read {page_number}/{len(pdf.pages)} pages", flush=True)
    missing_ids = sorted(set(range(1, 527)) - records.keys())
    if missing_ids:
        raise ValueError(f"Incomplete extraction; missing STT: {missing_ids}. Output was not written.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records[number] for number in sorted(records))
    temporary.replace(output_path)
    report_path = output_path.with_suffix(".cleaning_report.json")
    report_path.write_text(json.dumps({
        "input": str(input_path), "rows": len(records), "missing_policy": missing_policy,
        "note": "PDF '-' is unavailable. Zero is an explicit compatibility imputation.",
        "imputations": issues,
        "classification": "Largest energy contribution: protein*4, carbs*4, fat*9; protein wins ties.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} rows to {output_path}; {len(issues)} imputations. Report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=ROOT / "data/VTN_FCT_2007.pdf")
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "data/DataDSS_labeled.csv")
    parser.add_argument("--missing", choices=["zero", "error"], default="zero")
    args = parser.parse_args()
    try:
        convert(args.input, args.output, args.missing)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
