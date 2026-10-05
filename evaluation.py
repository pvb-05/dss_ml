import numpy as np
import matplotlib.pyplot as plt
from knn_model import get_recommendations


def evaluate_recommendations(target_dict, recommended_menus):
    # [Giữ nguyên ruột hàm evaluate_recommendations của bạn ở đây]
    target = np.array(
        [
            target_dict["calo"],
            target_dict["pro"],
            target_dict["carb"],
            target_dict["fat"],
        ]
    )
    preds = np.array(
        [
            [m["Total_Calories"], m["Total_Protein"], m["Total_Carbs"], m["Total_Fat"]]
            for m in recommended_menus
        ]
    )

    mae = np.mean(np.abs(preds - target), axis=0)
    rmse = np.sqrt(np.mean((preds - target) ** 2, axis=0))
    mape = np.mean(np.abs((preds - target) / target), axis=0) * 100

    print("\n" + "=" * 40)
    labels = ["Calories", "Protein", "Carbs", "Fat"]
    for i, label in enumerate(labels):
        print(
            f"[{label}] MAE: {mae[i]:.1f} | RMSE: {rmse[i]:.1f} | MAPE: {mape[i]:.2f}%"
        )

    return mape


if __name__ == "__main__":
    print("ĐANG CHẠY CÁC KỊCH BẢN KIỂM THỬ (TEST CASES)...\n")

    # Kịch bản 1: Nam, Tăng cơ
    print(">>> TEST CASE 1: Nam, 21 tuổi, mục tiêu Tăng cơ")
    data_1 = get_recommendations(
        age=21,
        weight_kg=65,
        height_cm=170,
        gender="nam",
        activity_level="vua",
        goal="tang_co",
    )
    mape_1 = evaluate_recommendations(data_1["target"], data_1["menus"])

    # Kịch bản 2: Nữ, Giảm mỡ
    print("\n>>> TEST CASE 2: Nữ, 22 tuổi, mục tiêu Giảm mỡ")
    data_2 = get_recommendations(
        age=22,
        weight_kg=55,
        height_cm=160,
        gender="nu",
        activity_level="it_van_dong",
        goal="giam_mo",
    )
    mape_2 = evaluate_recommendations(data_2["target"], data_2["menus"])

    # Kịch bản 3: Nam, Giữ dáng
    print("\n>>> TEST CASE 3: Nam, 25 tuổi, mục tiêu Giữ dáng")
    data_3 = get_recommendations(
        age=25,
        weight_kg=75,
        height_cm=175,
        gender="nam",
        activity_level="nhe",
        goal="giu_can",
    )
    mape_3 = evaluate_recommendations(data_3["target"], data_3["menus"])

    # ==========================================
    # VẼ BIỂU ĐỒ SO SÁNH SAI SỐ MAPE
    # ==========================================
    labels = ["Calories", "Protein", "Carbs", "Fat"]
    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width, mape_1, width, label="Test 1 (Tăng cơ)")
    rects2 = ax.bar(x, mape_2, width, label="Test 2 (Giảm mỡ)")
    rects3 = ax.bar(x + width, mape_3, width, label="Test 3 (Giữ dáng)")

    ax.set_ylabel("Sai số phần trăm (MAPE %)")
    ax.set_title("Đánh giá sai số thuật toán KNN trên các kịch bản người dùng")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig("evaluation_knn.png", dpi=300)
    plt.show()
