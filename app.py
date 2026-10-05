from flask import Flask, render_template, request
from knn_model import get_recommendations

app = Flask(__name__)

# Route cho trang chủ (Hiển thị Form)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Route xử lý kết quả khi người dùng bấm "Nhận gợi ý"
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Lấy dữ liệu từ Form HTML
        age = int(request.form['age'])
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        gender = request.form['gender']
        activity = request.form['activity']
        goal = request.form['goal']
        
        # Danh sách dị ứng
        allergies = request.form.getlist('allergies')

        # Gọi hàm chạy KNN
        data = get_recommendations(age, weight, height, gender, activity, goal)
        
        # Render kết quả ra trang result.html
        return render_template('result.html', target=data['target'], menus=data['menus'])
        
    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"

if __name__ == '__main__':
    # Bật debug mode để web tự load lại khi sửa code
    app.run(debug=True, port=5000)