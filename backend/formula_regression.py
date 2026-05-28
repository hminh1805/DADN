import pandas as pd
import numpy as np
import joblib
import json
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

MODE = "train"
MODEL1_PATH = "models/gradient_boosting.pkl" # Đổi path này để chọn model phù hợp
SCALER_PATH = "models/scaler.pkl"
FORMULA_PATH = "backend/formula.json"
DATA_PATH = "backend/my_data.csv"

# load 1 lần
model1 = joblib.load(MODEL1_PATH)
scaler = joblib.load(SCALER_PATH)

def calculate_heat_index(T_C, RH):
    T_F = T_C * 1.8 + 32
    HI_F = 0.5 * (T_F + 61.0 + ((T_F - 68.0) * 1.2) + (RH * 0.094))
    if T_F >= 80:
        HI_F = -42.379 + 2.04901523*T_F + 10.14333127*RH \
               - 0.22475541*T_F*RH - 0.00683783*(T_F**2) \
               - 0.05481717*(RH**2) + 0.00122874*(T_F**2)*RH \
               + 0.00085282*T_F*(RH**2) - 0.00000199*(T_F**2)*(RH**2)
    return (HI_F - 32) / 1.8

def build_features_batch(df):
    temp = df["temp"].values
    humidity = df["humidity"].values

    thom = temp - 0.55 * (1 - humidity / 100.0) * (temp - 14.5)
    dew_point = temp - ((100 - humidity) / 5)
    heat_index = np.array([calculate_heat_index(t, h) for t, h in zip(temp, humidity)])
    temp_dew_diff = temp - dew_point
    pmv = 0.303 * temp + 0.02 * humidity - 8.5

    return np.column_stack([
        temp,
        humidity,
        thom,
        dew_point,
        heat_index,
        pmv,
        temp_dew_diff
    ])

def train_formula():
    df = pd.read_csv(DATA_PATH)
    df.columns = ["temp", "humidity", "label"]

    print("Building features...")
    X_model1 = build_features_batch(df)

    print("Scaling...")
    X_model1_scaled = scaler.transform(X_model1)

    print("Predicting model 1...")
    predicted_labels = model1.predict(X_model1_scaled)

    X = df[["temp", "humidity"]]
    y = predicted_labels

    reg = LinearRegression()
    reg.fit(X, y)

    a = reg.coef_[0]
    b = reg.coef_[1]
    c = reg.intercept_

    pred_y = reg.predict(X)

    print("\n=== PHƯƠNG TRÌNH ===")
    print(f"x = {a:.4f} * temp + {b:.4f} * humidity + {c:.4f}")

    print("\n=== ĐÁNH GIÁ ===")
    print("MAE =", mean_absolute_error(y, pred_y))
    print("R2  =", r2_score(y, pred_y))

    with open(FORMULA_PATH, "w") as f:
        json.dump({"a": float(a), "b": float(b), "c": float(c)}, f, indent=4)

    print("\nSaved to", FORMULA_PATH)

if __name__ == "__main__":
    train_formula()