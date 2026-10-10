from numpy import indices
import pandas as pd
import sqlite3
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


def validate_user_input(
    age,
    weight_kg,
    height_cm,
    gender=None,
    activity_level=None,
    goal=None,
):
    # 1. Ràng buộc tuổi: số tự nhiên lớn hơn 0, nằm trong khoảng hợp lý (10 - 120 tuổi)
    if not isinstance(age, int) or age <= 0:
        raise ValueError("Độ tuổi phải là số tự nhiên lớn hơn 0.")
    if age < 10 or age > 120:
        raise ValueError(
            f"Độ tuổi không hợp lý ({age} tuổi). Vui lòng nhập từ 10 đến 120 tuổi."
        )

    # 2. Ràng buộc chiều cao: số dương, không âm, giới hạn hợp lý (50 - 250 cm)
    if not isinstance(height_cm, (int, float)) or height_cm <= 0:
        raise ValueError("Chiều cao phải là số dương lớn hơn 0.")
    if height_cm < 50 or height_cm > 250:
        raise ValueError(
            f"Chiều cao không hợp lý ({height_cm} cm). Vui lòng nhập từ 50 đến 250 cm."
        )

    # 3. Ràng buộc cân nặng: số dương, không âm, giới hạn hợp lý (20 - 300 kg)
    if not isinstance(weight_kg, (int, float)) or weight_kg <= 0:
        raise ValueError("Cân nặng phải là số dương lớn hơn 0.")
    if weight_kg < 20 or weight_kg > 300:
        raise ValueError(
            f"Cân nặng không hợp lý ({weight_kg} kg). Vui lòng nhập từ 20 đến 300 kg."
        )

    # 4. Ràng buộc giới tính
    if gender and str(gender).lower() not in ["nam", "nu"]:
        raise ValueError("Giới tính không hợp lệ (chỉ chấp nhận 'nam' hoặc 'nu').")

    # 5. Ràng buộc mức độ vận động
    valid_activities = ["it_van_dong", "nhe", "vua", "nhieu", "nang", "rat_nang"]
    if activity_level and activity_level not in valid_activities:
        raise ValueError("Mức độ vận động không hợp lệ.")

    # 6. Ràng buộc mục tiêu
    valid_goals = ["tang_co", "giam_mo", "giu_can"]
    if goal and goal not in valid_goals:
        raise ValueError("Mục tiêu tập luyện không hợp lệ.")


def get_recommendations(
    age,
    weight_kg,
    height_cm,
    gender,
    activity_level,
    goal,
    allergies=[],
    n_suggestions=5,
):
    # 0. KIỂM TRA RÀNG BUỘC ĐẦU VÀO
    validate_user_input(
        age=age,
        weight_kg=weight_kg,
        height_cm=height_cm,
        gender=gender,
        activity_level=activity_level,
        goal=goal,
    )

    # 1. TÍNH TOÁN USER TARGET
    if gender.lower() == "nam":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    activity_multipliers = {
        "it_van_dong": 1.2,
        "nhe": 1.375,
        "vua": 1.55,
        "nhieu": 1.725,
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)

    if goal == "tang_co":
        target_calories = tdee + 500
        p, c, f = 0.30, 0.50, 0.20
    elif goal == "giam_mo":
        target_calories = tdee - 500
        p, c, f = 0.40, 0.30, 0.30
    else:
        target_calories = tdee
        p, c, f = 0.30, 0.40, 0.30

    meal_calories = target_calories / 3

    # Tính toán số gram cụ thể cho 1 bữa
    query_vector = [
        meal_calories,
        (meal_calories * p) / 4,
        (meal_calories * c) / 4,
        (meal_calories * f) / 9,
    ]

    # Lọc thực phẩm dựa trên dị ứng
    base_query = "SELECT * FROM MenuTable WHERE 1=1"

    # Khớp từng keyword loại trừ dựa trên Tên Thực Phẩm lưu trong DB
    if "no_pork" in allergies:
        base_query += " AND Dam NOT LIKE '%lợn%' AND Dam NOT LIKE '%heo%'"

    if "no_beef" in allergies:
        base_query += " AND Dam NOT LIKE '%bò%'"

    if "no_seafood" in allergies:
        base_query += " AND Dam NOT LIKE '%cá%' AND Dam NOT LIKE '%tôm%' AND Dam NOT LIKE '%mực%' AND Dam NOT LIKE '%cua%'"

    if "no_peanut" in allergies:
        base_query += " AND Dam NOT LIKE '%lạc%' AND Rau NOT LIKE '%lạc%'"

    # 2. SINH DATASET & LOAD DATA
    conn = sqlite3.connect("data/fitness_menus.db")
    df_menus = pd.read_sql_query(base_query, conn)
    conn.close()

    # 3. CHẠY KNN
    features = ["Total_Calories", "Total_Protein", "Total_Carbs", "Total_Fat"]
    X = df_menus[features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    query_scaled = scaler.transform([query_vector])

    knn_model = NearestNeighbors(n_neighbors=n_suggestions, metric="euclidean")
    knn_model.fit(X_scaled)

    distances, indices = knn_model.kneighbors(query_scaled)

    results = []
    for idx in indices[0]:
        menu_dict = df_menus.iloc[idx].to_dict()

        # Thêm logic tính Độ khớp (%) để Trợ giúp ra quyết định
        sai_so_calo = (
            abs(menu_dict["Total_Calories"] - query_vector[0]) / query_vector[0]
        )
        do_khop = max(0, 100 - (sai_so_calo * 100))  # Không cho % âm
        menu_dict["Match_Percent"] = round(do_khop, 1)

        results.append(menu_dict)

    return {
        "target": {
            "calo": round(query_vector[0]),
            "pro": round(query_vector[1]),
            "carb": round(query_vector[2]),
            "fat": round(query_vector[3]),
        },
        "menus": results,
    }
