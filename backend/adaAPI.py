import os
import json
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv 
load_dotenv()
# ================= CẤU HÌNH ADAFRUIT IO =================
AIO_USERNAME = os.getenv("AIO_USERNAME", "your_name")
AIO_KEY = os.getenv("AIO_KEY", "your_key")

FEEDS = {
    "sensor": f"{AIO_USERNAME}/feeds/sensor",
    "motion": f"{AIO_USERNAME}/feeds/motion",
    "pet_detected": f"{AIO_USERNAME}/feeds/pet-detected",
    "pump": f"{AIO_USERNAME}/feeds/maybom",
    "speaker": f"{AIO_USERNAME}/feeds/led",
    "pet_feeder": f"{AIO_USERNAME}/feeds/servo",
    "fan": f"{AIO_USERNAME}/feeds/quat",
    "heater": f"{AIO_USERNAME}/feeds/heater",
}

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(AIO_USERNAME, AIO_KEY)

_callback_nhan_tin_nhan = None

def now_ms():
    return int(time.time() * 1000)

# ================= BỘ LỌC DỮ LIỆU ĐA NĂNG =================
def loc_du_lieu_sensor(payload):

    # TRƯỜNG HỢP 1: Nhận được JSON chuẩn (từ Gateway Python gửi lên)
    try:
        raw = json.loads(payload)
        return {
            "temperature": float(raw.get("nhiet_do", raw.get("temperature", 0))),
            "humidity": float(raw.get("do_am", raw.get("humidity", 0))),
            "water_level": float(raw.get("muc_nuoc", raw.get("water_level", 0))),
            "motion": bool(raw.get("motion", False), default=False),
            "distance": float(raw.get("distance", raw.get("dis", 0)), default=0.0),
            "timestamp": now_ms()
        }
    except json.JSONDecodeError:
        pass # Không phải JSON, đi tiếp sang Trường hợp 2

    # TRƯỜNG HỢP 2: Nhận được String do bo mạch phát thẳng WiFi
    try:
        clean_str = payload.replace("#", "").replace("!", "").strip()
        parts = []
        if "-" in clean_str:     # Ví dụ: "28.5-65-80-10"
            parts = clean_str.split("-")
        elif ":" in clean_str:   # Ví dụ: "28.5:65:80:10"
            parts = clean_str.split(":")
        if len(parts) >= 5:
            # Ví dụ string từ mạch: RT:RH:SM:motion:dis
            return {
                "temperature": _to_float(parts[0]),
                "humidity": _to_float(parts[1]),
                "water_level": _to_float(parts[2]),
                "motion": _to_bool(parts[3], default=False),
                "distance": _to_float(parts[4]),
                "timestamp": now_ms(),
            }
    except Exception as e:
        print(f"[AdaAPI] Đã lọc bỏ vì data không đúng: {payload} -> Lỗi: {e}")
        return None
    
    return None

# ================= HÀM LẮNG NGHE CHÍNH =================
def on_connect(client, userdata, flags, rc):
    print(f"[AdaAPI] Connected to Adafruit IO, rc = {rc}")
    for feed_name, topic in FEEDS.items():
        client.subscribe(topic)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    
    feed_key = None
    for key, val in FEEDS.items():
        if val == topic:
            feed_key = key
            break

    if _callback_nhan_tin_nhan and feed_key:
        if feed_key == "sensor":
            data_sach = loc_du_lieu_sensor(payload)
            if data_sach:
                # Đưa Dictionary qua cho App.py
                _callback_nhan_tin_nhan(feed_key, data_sach) 
            else:
                print("[AdaAPI] Từ chối giao hàng vì sensor data rác!")
        else:
            # Các feed nút bấm (1, 0) thì cứ giao string bình thường
            _callback_nhan_tin_nhan(feed_key, payload)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt(ham_xu_ly=None):
    global _callback_nhan_tin_nhan
    _callback_nhan_tin_nhan = ham_xu_ly
    print("[AdaAPI] Khởi động MQTT Client...")
    mqtt_client.connect("io.adafruit.com", 1883, 60)
    mqtt_client.loop_start()

def publish_data(feed_key, payload):
    if feed_key in FEEDS:
        topic = FEEDS[feed_key]
        mqtt_client.publish(topic, str(payload))
        print(f"[AdaAPI] Gửi lên {feed_key}: {payload}")
