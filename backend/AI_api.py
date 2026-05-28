import joblib
import numpy as np
import os
import csv



scaler = joblib.load("models/scaler.pkl")
rf_model = joblib.load("models/gradient_boosting.pkl")  
def predict_thermal_comfort(temp, humidity):
    # Tính toán lại các feature y hệt lúc train AI
    thom = temp - 0.55 * (1 - humidity / 100.0) * (temp - 14.5)
    dew_point = temp - ((100 - humidity) / 5)
    
    T_F = temp * 1.8 + 32
    HI_F = 0.5 * (T_F + 61.0 + ((T_F - 68.0) * 1.2) + (humidity * 0.094))
    if T_F >= 80:
         HI_F = -42.379 + 2.04901523*T_F + 10.14333127*humidity - 0.22475541*T_F*humidity - 0.00683783*(T_F**2) - 0.05481717*(humidity**2) + 0.00122874*(T_F**2)*humidity + 0.00085282*T_F*(humidity**2) - 0.00000199*(T_F**2)*(humidity**2)
    heat_index = (HI_F - 32) / 1.8
    
    pmv = 0.303 * temp + 0.02 * humidity - 8.5
    temp_dew_diff = temp - dew_point
    
    # Tạo mảng data và Scale
    features = np.array([[temp, humidity, thom, dew_point, heat_index, pmv, temp_dew_diff]])
    features_scaled = scaler.transform(features)
    
    # Dự đoán trả về: -1 (Lạnh), 0 (Bình thường), 1 (Ấm), 2 (Nóng)
    prediction = rf_model.predict(features_scaled)[0]
    return prediction



def save_my_data(temp , humidity, label):
    file_path = "my_data.csv"
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            # Tạo tiêu đề cột nếu file chưa tồn tại
            writer.writerow(["temp", "humidity", "label"])
        writer.writerow([temp, humidity, label])
        
        
