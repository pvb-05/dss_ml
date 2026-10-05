import numpy as np
from knn_model import get_recommendations

def evaluate_recommendations(target_dict, recommended_menus):
    # 1. Chuyển đổi dictionary mục tiêu thành mảng NumPy
    target = np.array([
        target_dict['calo'], 
        target_dict['pro'], 
        target_dict['carb'], 
        target_dict['fat']
    ])
    
    # 2. Rút trích các chỉ số dinh dưỡng từ Top 5 thực đơn gợi ý
    preds = []
    for menu in recommended_menus:
        preds.append([
            menu['Total_Calories'],
            menu['Total_Protein'],
            menu['Total_Carbs'],
            menu['Total_Fat']
        ])
    preds = np.array(preds)
    
    # 3. Tính toán các chỉ số sai số
    mae = np.mean(np.abs(preds - target), axis=0)
    rmse = np.sqrt(np.mean((preds - target)**2, axis=0))
    mape = np.mean(np.abs((preds - target) / target), axis=0) * 100
    
    # 4. In báo cáo ra màn hình (Console)
    print("BÁO CÁO ĐÁNH GIÁ MÔ HÌNH KNN \n")
    
    labels = ['Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)']
    for i, label in enumerate(labels):
        print(f"[{label}]")
        print(f" - MAE  (Lệch tuyệt đối trung bình): {mae[i]:.1f}")
        print(f" - RMSE (Độ lệch chuẩn)             : {rmse[i]:.1f}")
        print(f" - MAPE (% Sai số trung bình)       : {mape[i]:.2f} %\n")
        
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}

if __name__ == "__main__":
    print("Đang chạy mô hình KNN để lấy dữ liệu Test...")
    
    # Kịch bản Test 1: Nam sinh viên, 21 tuổi, cao 170cm, nặng 65kg, tập vừa, mục tiêu Tăng cơ
    data_test_1 = get_recommendations(
        age=21, 
        weight_kg=65, 
        height_cm=170, 
        gender='nam', 
        activity_level='vua', 
        goal='tang_co'
    )
    
    print(f"\nMỤC TIÊU CỦA USER 1: {data_test_1['target']}")
    evaluate_recommendations(data_test_1['target'], data_test_1['menus'])
    
    # Bạn có thể copy cụm trên để chạy thêm Kịch bản Test 2 (Nữ, giảm mỡ...) để làm phong phú báo cáo