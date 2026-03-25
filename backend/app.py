import json
import os
import threading
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from data_manager import add_activity, load_data, save_data, update_device, update_sensors
import adaAPI


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ================= CẤU HÌNH ADAFRUIT IO =================
# AIO_USERNAME = os.getenv("AIO_USERNAME", "your_name")
# AIO_KEY = os.getenv("AIO_KEY", "your_key")

# SENSOR_FEED = f"{AIO_USERNAME}/feeds/sensor"
# MOTION_FEED = f"{AIO_USERNAME}/feeds/motion"
# PET_DETECTED_FEED = f"{AIO_USERNAME}/feeds/pet-detected"

# CONTROL_FEEDS = {
#     "pump": f"{AIO_USERNAME}/feeds/maybom",
#     "speaker": f"{AIO_USERNAME}/feeds/led",
#     "pet_feeder": f"{AIO_USERNAME}/feeds/servo",
#     "fan": f"{AIO_USERNAME}/feeds/quat",
#     "heater": f"{AIO_USERNAME}/feeds/heater",
# }

AUTHORIZED_PET = os.getenv("AUTHORIZED_PET", "dog")
AUTO_FAN_ON = 30.0
AUTO_HEATER_ON = 20.0
AUTO_WATER_REFILL_THRESHOLD = 20.0

# mqtt_client = mqtt.Client()
# mqtt_client.username_pw_set(AIO_USERNAME, AIO_KEY)


def now_ms():
    return int(datetime.utcnow().timestamp() * 1000)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "on", "open", "yes"}


def publish_device_status():
    socketio.emit("device_status", load_data()["devices"])


def publish_sensor_update():
    socketio.emit("sensor_update", load_data()["sensors"])


def add_realtime_activity(activity_type, message):
    add_activity(activity_type, message)
    socketio.emit(
        "alert",
        {
            "id": str(now_ms()),
            "type": activity_type,
            "title": "PawHome Alert",
            "message": message,
            "timestamp": now_ms(),
        },
    )


def _set_device_state(device, on):
    update_device(device, on)
    publish_device_status()


def _timed_toggle(device, duration_sec):
    _set_device_state(device, True)
    def _set_device_state_after():
        _set_device_state(device, False)
        _send_to_feed(device, "0")
        
    threading.Timer(duration_sec, lambda: _set_device_state_after()).start()


def _send_to_feed(feed_key, payload):     
        adaAPI.publish_data(feed_key, payload)


def execute_command(device, action):
    # Tương thích ngược với dữ liệu cũ (dog_feeder/cat_feeder)
    if device in {"dog_feeder", "cat_feeder"}:
        device = "pet_feeder"

    if device not in adaAPI.FEEDS:
        return False, "Thiết bị không hợp lệ."

    if device == "pet_feeder" and action == "dispense":
        _send_to_feed(device, "1")
        _timed_toggle(device, 2.0)
        add_activity("success", "Đã nhả thức ăn cho thú cưng.")
        return True, "Đã nhả thức ăn cho thú cưng."

    if device == "pump" and action == "refill":
        _send_to_feed(device, "1")
        _timed_toggle("pump", 4.0)
        add_activity("info", "Đã bật bơm refill nước tự động.")
        return True, "Đã bật bơm refill nước."

    if action in {"on", "off"}:
        raw = "1" if action == "on" else "0"
        _send_to_feed(device, raw)
        _set_device_state(device, action == "on")
        add_activity("info", f"Thiết bị {device} -> {action.upper()}.")
        return True, f"Đã gửi lệnh {action.upper()} cho {device}."

    return False, "Action không hợp lệ."


def run_auto_logic(sensor_data):
    data = load_data()
    if data["mode"] != "auto":
        return

    temp = float(sensor_data.get("temperature", 0))
    water_level = float(sensor_data.get("water_level", 0))
    motion = _to_bool(sensor_data.get("motion", False))
    pet = sensor_data.get("pet_detected")

    # if temp > AUTO_FAN_ON:
    #     execute_command("fan", "on")
    #     execute_command("heater", "off")
    # elif temp < AUTO_HEATER_ON:
    #     execute_command("fan", "off")
    #     execute_command("heater", "on")
    # else:
    #     execute_command("fan", "off")
    #     execute_command("heater", "off")

    # if water_level < AUTO_WATER_REFILL_THRESHOLD and not data["devices"]["pump"]:
    #     execute_command("pump", "refill")

    if motion:
        execute_command("speaker", "on")
        threading.Timer(3.0, lambda: execute_command("speaker", "off")).start()
        add_realtime_activity("warning", "Phát hiện chuyển động ở khu vực cấm.")

    if pet in {"dog", "cat"}:
        socketio.emit("pet_detected", {"pet": pet, "confidence": 1.0, "timestamp": now_ms()})
        if pet == AUTHORIZED_PET:
            execute_command("pet_feeder", "dispense")
        else:
            add_realtime_activity("warning", f"Nhận diện {pet} không đúng cấu hình cho phép.")




# --- DÁN CỤC NÀY VÀO CHỖ VỪA XÓA ---
# lấy dữ liệu từ ada
def xu_ly_tin_nhan_mqtt(feed_key, payload):
    """
    Đây là TỔNG ĐÀI MỚI.
    Thằng shipper adaAPI.py cứ có hàng là nó sẽ réo gọi cái hàm này và ném data vào 'payload'.
    """
    print(f"🎯 [App.py] Đã nhận hàng từ shipper adaAPI - Feed: {feed_key} | Data: {payload}")

    if feed_key == "sensor":
        # Nhờ adaAPI lọc hộ rồi, nên 'payload' lúc này chắc chắn 100% là Dictionary (JSON)
        # Không cần dùng hàm parse_gateway_sensor() nữa, cứ thế mà xài thẳng luôn!
        update_sensors(payload)
        publish_sensor_update()
        run_auto_logic(payload)

    elif feed_key == "motion":
        update_sensors({"motion": _to_bool(payload), "timestamp": now_ms()})
        publish_sensor_update()
        run_auto_logic(load_data()["sensors"])

    elif feed_key == "pet_detected":
        pet = payload.lower() if payload.lower() in {"dog", "cat"} else None
        update_sensors({"pet_detected": pet, "timestamp": now_ms()})
        publish_sensor_update()
        run_auto_logic(load_data()["sensors"])

# Ra lệnh cho thằng adaAPI bắt đầu chạy, và đưa cái hàm "Tổng đài" này cho nó giữ
adaAPI.start_mqtt(ham_xu_ly=xu_ly_tin_nhan_mqtt)


@app.route("/api/sensors/latest", methods=["GET"])
def get_latest_sensor():
    return jsonify(load_data()["sensors"])


@app.route("/api/devices/status", methods=["GET"])
def get_device_status():
    return jsonify(load_data()["devices"])


@app.route("/api/devices/command", methods=["POST"])
def command_device():
    payload = request.get_json(silent=True) or {}
    device = payload.get("device")
    action = payload.get("action")

    ok, message = execute_command(device, action)
    code = 200 if ok else 400
    return jsonify({"success": ok, "message": message}), code


@app.route("/api/activities", methods=["GET"])
def get_activities():
    return jsonify(load_data()["activities"])


@app.route("/api/mode", methods=["POST"])
def change_mode():
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode")
    if mode not in {"auto", "manual"}:
        return jsonify({"success": False, "message": "Mode không hợp lệ."}), 400

    data = load_data()
    data["mode"] = mode
    save_data(data)
    add_activity("info", f"Chuyển chế độ hệ thống sang {mode}.")
    return jsonify({"success": True, "message": f"Đã chuyển sang {mode}."})