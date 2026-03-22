import json
import os
import threading
from datetime import datetime

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from data_manager import add_activity, load_data, save_data, update_device, update_sensors

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ================= CẤU HÌNH ADAFRUIT IO =================
AIO_USERNAME = os.getenv("AIO_USERNAME", "your_name")
AIO_KEY = os.getenv("AIO_KEY", "your_key")

SENSOR_FEED = f"{AIO_USERNAME}/feeds/sensor"
PET_DETECTED_FEED = f"{AIO_USERNAME}/feeds/pet-detected"

CONTROL_FEEDS = {
    "pump": f"{AIO_USERNAME}/feeds/maybom",
    "speaker": f"{AIO_USERNAME}/feeds/led",
    "pet_feeder": f"{AIO_USERNAME}/feeds/servo",
    "fan": f"{AIO_USERNAME}/feeds/quat",
    "heater": f"{AIO_USERNAME}/feeds/heater",
}

AUTHORIZED_PET = os.getenv("AUTHORIZED_PET", "dog")
AUTO_FAN_ON = 30.0
AUTO_HEATER_ON = 20.0
AUTO_WATER_REFILL_THRESHOLD = 20.0

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(AIO_USERNAME, AIO_KEY)


def now_ms():
    return int(datetime.utcnow().timestamp() * 1000)


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
    threading.Timer(duration_sec, lambda: _set_device_state(device, False)).start()


def _send_to_feed(feed_key, payload):
    mqtt_client.publish(CONTROL_FEEDS[feed_key], payload)


def execute_command(device, action):
    # Tương thích ngược với dữ liệu cũ (dog_feeder/cat_feeder)
    if device in {"dog_feeder", "cat_feeder"}:
        device = "pet_feeder"

    if device not in CONTROL_FEEDS:
        return False, "Thiết bị không hợp lệ."

    if device == "pet_feeder" and action == "dispense":
        _send_to_feed(device, "DISPENSE")
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
    pet = sensor_data.get("pet_detected")

    if temp > AUTO_FAN_ON:
        execute_command("fan", "on")
        execute_command("heater", "off")
    elif temp < AUTO_HEATER_ON:
        execute_command("fan", "off")
        execute_command("heater", "on")
    else:
        execute_command("fan", "off")
        execute_command("heater", "off")

    if water_level < AUTO_WATER_REFILL_THRESHOLD and not data["devices"]["pump"]:
        execute_command("pump", "refill")

    if pet in {"dog", "cat"}:
        socketio.emit("pet_detected", {"pet": pet, "confidence": 1.0, "timestamp": now_ms()})
        if pet == AUTHORIZED_PET:
            execute_command("pet_feeder", "dispense")
        else:
            add_realtime_activity("warning", f"Nhận diện {pet} không đúng cấu hình cho phép.")


# ── Định dạng giống gateway (Adafruit feed "sensor") ─────────────────
# JSON từ gateway.publish: luôn là object với đúng 4 key:
#   nhiet_do, do_am, muc_nuoc, anh_sang
# (mock gateway: thong_so = { nhiet_do, do_am, muc_nuoc, anh_sang })
# Chuỗi từ mạch (nếu gửi thẳng lên MQTT): !nhiet_do:do_am:muc_nuoc:anh_sang#
#   — giống gateway processData (bản cũ)


def _gateway_json_to_internal(raw: dict):
    """Map JSON gateway → schema nội bộ / API cho frontend."""
    if not isinstance(raw, dict):
        return None
    default_food = float(raw.get("anh_sang", 0))
    return {
        "temperature": float(raw.get("nhiet_do", 0)),
        "humidity": float(raw.get("do_am", 0)),
        "water_level": float(raw.get("muc_nuoc", 0)),
        "dog_food": float(raw.get("dog_food", default_food)),
        "cat_food": float(raw.get("cat_food", default_food)),
        "timestamp": now_ms(),
    }


def _parse_sensor_serial(payload: str):
    """!nhiet_do:do_am:muc_nuoc:anh_sang# — giống gateway processData (bản cũ)."""
    s = payload.strip()
    if "!" in s and "#" in s:
        start, end = s.find("!"), s.find("#")
        if start < end:
            s = s[start + 1 : end]
    else:
        s = s.replace("!", "").replace("#", "").strip()
    parts = [p.strip() for p in s.split(":") if p.strip() != ""]
    if len(parts) != 4:
        return None
    try:
        nhiet_do = float(parts[0])
        do_am = float(parts[1])
        muc_nuoc = float(parts[2])
        anh_sang = float(parts[3])
    except ValueError:
        return None
    return _gateway_json_to_internal(
        {
            "nhiet_do": nhiet_do,
            "do_am": do_am,
            "muc_nuoc": muc_nuoc,
            "anh_sang": anh_sang,
        }
    )


def parse_sensor_payload(payload: str):
    """
    - JSON (Adafruit / gateway): {"nhiet_do","do_am","muc_nuoc","anh_sang"}
    - Chuỗi mạch: !a:b:c:d# (thứ tự như gateway)
    """
    payload = (payload or "").strip()
    if not payload:
        return None

    if payload[0] in "{[":
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError:
            return None
        return _gateway_json_to_internal(raw)

    if "!" in payload and "#" in payload:
        return _parse_sensor_serial(payload)

    try:
        raw = json.loads(payload)
        return _gateway_json_to_internal(raw)
    except json.JSONDecodeError:
        return None


def on_connect(client, userdata, flags, rc):
    print("Connected Adafruit IO, rc =", rc)
    client.subscribe(SENSOR_FEED)
    client.subscribe(PET_DETECTED_FEED)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    print(f"[MQTT] {topic}: {payload}")

    if topic == SENSOR_FEED:
        sensor_payload = parse_sensor_payload(payload)
        if sensor_payload:
            update_sensors(sensor_payload)
            publish_sensor_update()
            run_auto_logic(sensor_payload)
        else:
            print(f"[sensor] Bỏ qua payload không hợp lệ: {payload!r}")
        return

    if topic == PET_DETECTED_FEED:
        pet = payload.lower() if payload.lower() in {"dog", "cat"} else None
        update_sensors({"pet_detected": pet, "timestamp": now_ms()})
        publish_sensor_update()
        run_auto_logic(load_data()["sensors"])


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def start_mqtt():
    mqtt_client.connect("io.adafruit.com", 1883, 60)
    mqtt_client.loop_start()


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