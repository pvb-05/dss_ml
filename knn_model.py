import pandas as pd
import sqlite3
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

def get_recommendations(age, weight_kg, height_cm, gender, activity_level, goal, allergies=[], n_suggestions=5):
    # 1. TÍNH TOÁN USER TARGET
    if gender.lower() == 'nam':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
    activity_multipliers = {'it_van_dong': 1.2, 'nhe': 1.375, 'vua': 1.55, 'nhieu': 1.725}
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)
    
    if goal == 'tang_co':
        target_calories = tdee + 500
        p, c, f = 0.30, 0.50, 0.20
    elif goal == 'giam_mo':
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
            (meal_calories * f) / 9
    ]

    # Lọc thực phẩm dựa trên dị ứng
    base_query = "SELECT * FROM MenuTable WHERE 1=1"
    
    # Khớp từng keyword loại trừ dựa trên Tên Thực Phẩm lưu trong DB
    if 'no_pork' in allergies:
        base_query += " AND Dam NOT LIKE '%lợn%' AND Dam NOT LIKE '%heo%'"
    
    if 'no_beef' in allergies:
        base_query += " AND Dam NOT LIKE '%bò%'"
        
    if 'no_seafood' in allergies:
        base_query += " AND Dam NOT LIKE '%cá%' AND Dam NOT LIKE '%tôm%' AND Dam NOT LIKE '%mực%' AND Dam NOT LIKE '%cua%'"
        
    if 'no_peanut' in allergies:
        base_query += " AND Dam NOT LIKE '%lạc%' AND Rau NOT LIKE '%lạc%'"

    # 2. SINH DATASET & LOAD DATA
    conn = sqlite3.connect('data/fitness_menus.db')
    df_menus = pd.read_sql_query(base_query, conn)
    conn.close()

    # 3. CHẠY KNN
    features = ['Total_Calories', 'Total_Protein', 'Total_Carbs', 'Total_Fat']
    X = df_menus[features]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    query_scaled = scaler.transform([query_vector])
    
    knn_model = NearestNeighbors(n_neighbors=n_suggestions, metric='euclidean')
    knn_model.fit(X_scaled)
    
    distances, indices = knn_model.kneighbors(query_scaled)
    
    results = []
    for idx in indices[0]:
        results.append(df_menus.iloc[idx].to_dict())
        
    return {
        'target': {'calo': round(query_vector[0]), 'pro': round(query_vector[1]), 'carb': round(query_vector[2]), 'fat': round(query_vector[3])},
        'menus': results
    }
