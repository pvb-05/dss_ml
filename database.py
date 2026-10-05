import pandas as pd
import random
import sqlite3
import os


def create_menu_database(db_name="fitness_menus.db", num_menus=20000):
    print("1. Đang đọc dữ liệu nguyên liệu...")
    df = pd.read_csv("data/DataDSS_labeled.csv")
    df = df[df["Nhóm Đa lượng chính"] != "Không xác định"]

    ro_tinh_bot = df[
        (df["Nhóm Đa lượng chính"] == "Carb-rich")
        & (df["Nhóm thực phẩm"].str.contains("Ngũ cốc|Khoai củ", na=False, case=False))
    ]
    ro_dam = df[df["Nhóm Đa lượng chính"] == "Protein-rich"]
    ro_rau = df[df["Nhóm thực phẩm"] == "Rau, quả, củ dùng làm rau"]

    print(f"2. Đang sinh {num_menus} tổ hợp thực đơn. Vui lòng đợi...")
    menus = []
    for i in range(num_menus):
        t = ro_tinh_bot.sample(1).iloc[0]
        d = ro_dam.sample(1).iloc[0]
        r = ro_rau.sample(1).iloc[0]

        gt = random.choice([100, 150, 200, 250])
        gd = random.choice([150, 200, 250, 300])
        gr = random.choice([100, 150, 200, 250])

        menus.append(
            {
                "Menu_ID": f"M_{i+1}",
                "Tinh_Bot": f"{t['Tên Thực Phẩm']} ({gt}g)",
                "Dam": f"{d['Tên Thực Phẩm']} ({gd}g)",
                "Rau": f"{r['Tên Thực Phẩm']} ({gr}g)",
                "Total_Calories": round(
                    t["Calories (kcal)"] * gt / 100
                    + d["Calories (kcal)"] * gd / 100
                    + r["Calories (kcal)"] * gr / 100,
                    1,
                ),
                "Total_Protein": round(
                    t["Protein (g)"] * gt / 100
                    + d["Protein (g)"] * gd / 100
                    + r["Protein (g)"] * gr / 100,
                    1,
                ),
                "Total_Carbs": round(
                    t["Carbs (g)"] * gt / 100
                    + d["Carbs (g)"] * gd / 100
                    + r["Carbs (g)"] * gr / 100,
                    1,
                ),
                "Total_Fat": round(
                    t["Fat (g)"] * gt / 100
                    + d["Fat (g)"] * gd / 100
                    + r["Fat (g)"] * gr / 100,
                    1,
                ),
            }
        )

    df_menus = pd.DataFrame(menus)

    print("3. Đang ghi vào Database SQLite...")
    # Kết nối và tự động tạo file database nếu chưa có
    conn = sqlite3.connect(db_name)

    # Pandas hỗ trợ ghi thẳng DataFrame thành một Table trong SQLite
    # if_exists='replace' giúp ghi đè nếu bạn muốn chạy lại file này để tạo thực đơn mới
    df_menus.to_sql("MenuTable", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print(f"Hoàn tất! Database '{db_name}' đã sẵn sàng.")


if __name__ == "__main__":
    create_menu_database()
