from flask import Flask, render_template, request
from knn_model import get_recommendations
import json

app = Flask(__name__)


# Route cho trang chủ (Hiển thị Form)
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Route xử lý kết quả khi người dùng bấm "Nhận gợi ý"
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Lấy dữ liệu từ Form HTML
        raw_age = request.form.get("age", "").strip()
        raw_weight = request.form.get("weight", "").strip()
        raw_height = request.form.get("height", "").strip()
        gender = request.form.get("gender", "").strip()
        activity = request.form.get("activity", "").strip()
        goal = request.form.get("goal", "").strip()
        allergies = request.form.getlist("allergies")

        # Kiểm tra kiểu dữ liệu trước khi ép kiểu
        if not raw_age:
            raise ValueError("Vui lòng nhập độ tuổi.")
        try:
            age = int(raw_age)
        except ValueError:
            raise ValueError("Độ tuổi phải là một số tự nhiên (không chứa chữ hay số thập phân).")

        if not raw_height:
            raise ValueError("Vui lòng nhập chiều cao.")
        try:
            height = float(raw_height)
        except ValueError:
            raise ValueError("Chiều cao phải là một số hợp lệ.")

        if not raw_weight:
            raise ValueError("Vui lòng nhập cân nặng.")
        try:
            weight = float(raw_weight)
        except ValueError:
            raise ValueError("Cân nặng phải là một số hợp lệ.")

        # Gọi hàm chạy KNN (hàm này sẽ kiểm tra chi tiết các ràng buộc hợp lý)
        data = get_recommendations(age, weight, height, gender, activity, goal, allergies)

        # Render kết quả ra trang meals.html
        return render_template(
            "meals.html", target=data["target"], menus=data["menus"]
        )

    except ValueError as ve:
        return render_template(
            "index.html", error=str(ve), form_data=request.form
        ), 400
    except Exception as e:
        return render_template(
            "index.html", error=f"Đã xảy ra lỗi: {str(e)}", form_data=request.form
        ), 500


@app.route("/finalize", methods=["POST"])
def finalize():
    try:
        selected_meals = {}
        total_day_calo = total_day_pro = total_day_carb = total_day_fat = 0

        # Quét 5 menu gửi lên từ Form để xem người dùng đã gán menu nào vào Sáng/Trưa/Tối
        for i in range(5):
            choice = request.form.get(f"meal_choice_{i}")
            if choice and choice in ["Sáng", "Trưa", "Tối"]:
                # Giải mã dữ liệu JSON ẩn của thực đơn đó
                menu_data = json.loads(request.form.get(f"menu_data_{i}"))
                selected_meals[choice] = menu_data

                # Cộng dồn chỉ số 1 ngày
                total_day_calo += menu_data["Total_Calories"]
                total_day_pro += menu_data["Total_Protein"]
                total_day_carb += menu_data["Total_Carbs"]
                total_day_fat += menu_data["Total_Fat"]

        # Lấy mục tiêu 1 ngày (đã truyền ngầm từ trang trước)
        day_target = {
            "calo": float(request.form.get("day_target_calo")),
            "pro": float(request.form.get("day_target_pro")),
            "carb": float(request.form.get("day_target_carb")),
            "fat": float(request.form.get("day_target_fat")),
        }

        day_total = {
            "calo": round(total_day_calo, 1),
            "pro": round(total_day_pro, 1),
            "carb": round(total_day_carb, 1),
            "fat": round(total_day_fat, 1),
        }

        return render_template(
            "result.html",
            selected_meals=selected_meals,
            day_target=day_target,
            day_total=day_total,
        )

    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
