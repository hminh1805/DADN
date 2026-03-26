import json
import os
import threading
from datetime import datetime

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from data_manager import add_activity, load_data, save_data, should_refill_food, update_device, update_sensors
import adaAPI

AUTO_FAN_ON = 30
AUTO_HEATER_ON = 22
AUTO_OFF = 26
AUTO_REFILL = 30
AUTHORIZED_PET = 'dog'

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def now_ms():
    return int(datetime.utcnow().timestamp() * 1000)

def to_bool(v, default=False):
    if v == "1":
        return True
    if v == "0":
        return False
    return default

def clamp(v, lo, hi):
    try:
        v = float(v)
    except Exception:
        v = lo
    return max(lo, min(hi, v))

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


def set_device_state(device, on):
    update_device(device, on)
    publish_device_status()


def timed_toggle(device, duration_sec, feed_key=None):
    feed_key = feed_key or device
    set_device_state(device, True)
    def set_device_state_after():
        set_device_state(device, False)
        send_to_feed(feed_key, "0")
        
    threading.Timer(duration_sec, lambda: set_device_state_after()).start()


def send_to_feed(feed_key, payload):     
        adaAPI.publish_data(feed_key, payload)


def execute_command(device, action):
    requested_device = device
    food_inventory_key = None
    food_name = None
    feed_device = device
    state_device = device

    if device in {"dog_feeder", "cat_feeder"}:
        state_device = device
        feed_device = "pet_feeder"
        food_inventory_key = "dog_food" if requested_device == "dog_feeder" else "cat_food"
        food_name = "Buddy" if requested_device == "dog_feeder" else "Mochi"
        device = "pet_feeder"

    if requested_device == "servo":
        state_device = "servo"
        feed_device = "pet_feeder"
        device = "pet_feeder"
        if action != "dispense":
            return False, "Action không hợp lệ cho servo."

    if feed_device not in adaAPI.FEEDS:
        return False, "Thiết bị không hợp lệ."

    if device == "pet_feeder" and action == "dispense":
        send_to_feed(feed_device, "1")
        timed_toggle(state_device, 2.0, feed_key=feed_device)
        keys_to_update = []
        if requested_device in {"dog_feeder", "cat_feeder"} and food_inventory_key:
            keys_to_update = [food_inventory_key]
        elif requested_device == "servo":
            keys_to_update = ["dog_food", "cat_food"]

        if keys_to_update:
            updates = {}
            for k in keys_to_update:
                data = load_data()
                current = float(data["sensors"].get(k, 0.0))
                updates[k] = clamp(current + 15, 0, 100)
            updates["timestamp"] = now_ms()
            update_sensors(updates)
            publish_sensor_update()

        msg = (
            f"Đã refill thức ăn cho {food_name or 'thú cưng'}."
            if action == "refill"
            else f"Đã nhả thức ăn cho {food_name or 'thú cưng'}."
        )
        add_activity("success", msg)
        return True, msg

    if device == "pump" and action == "refill":
        send_to_feed(device, "1")
        timed_toggle("pump", 4.0)
        add_activity("info", "Đã bật bơm refill nước tự động.")
        return True, "Đã bật bơm refill nước."

    if action in {"on", "off"}:
        raw = "1" if action == "on" else "0"
        send_to_feed(device, raw)
        set_device_state(device, action == "on")
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
    motion = to_bool(sensor_data.get("motion", data["sensors"].get("motion", False)), default=False)
    distance_food_pct = float(sensor_data.get("distance", data["sensors"].get("distance", 0.0)))
    update_sensors({
        "dog_food": clamp(distance_food_pct, 0, 100),
        "cat_food": clamp(distance_food_pct, 0, 100),
        "timestamp": now_ms(),
    })
    publish_sensor_update()

    if distance_food_pct < 0.3:
        add_realtime_activity("warning", f"Thức ăn còn {round(distance_food_pct)}% (< 30%), bắt đầu nhả")
        execute_command("servo", "dispense")
        add_realtime_activity("info", "Đã nhả thức ăn cho cả dog_food và cat_food.")

    if temp >= AUTO_FAN_ON:
        execute_command("fan", "on")
        execute_command("heater", "off")

    if temp <= AUTO_HEATER_ON:
        execute_command("heater", "on")
        execute_command("fan", "off")
    
    if round(temp) == AUTO_OFF:
        execute_command("fan", "off")
        execute_command("heater", "off")

    if water_level < AUTO_REFILL and not data["devices"]["pump"]:
        execute_command("pump", "refill")

    if motion:
        execute_command("speaker", "on")
        threading.Timer(3.0, lambda: execute_command("speaker", "off")).start()
        add_realtime_activity("warning", "Phát hiện chuyển động ở khu vực cấm.")

    if pet in {"dog", "cat"}:
        socketio.emit("pet_detected", {"pet": pet, "confidence": 1.0, "timestamp": now_ms()})
        if pet == AUTHORIZED_PET:
            feeder_device = "dog_feeder" if pet == "dog" else "cat_feeder"
            execute_command(feeder_device, "dispense")
        else:
            add_realtime_activity("warning", f"Nhận diện {pet} không đúng cấu hình cho phép.")


# lấy dữ liệu từ ada
def xu_ly_tin_nhan_mqtt(feed_key, payload):
    print(f"[App.py] Đã nhận hàng từ shipper adaAPI - Feed: {feed_key} | Data: {payload}")

    if feed_key == "sensor":
        update_sensors(payload)
        publish_sensor_update()
        run_auto_logic(payload)

    elif feed_key == "motion":
        update_sensors({"motion": to_bool(payload), "timestamp": now_ms()})
        publish_sensor_update()
        run_auto_logic(load_data()["sensors"])

    elif feed_key == "pet_detected":
        pet = payload.lower() if payload.lower() in {"dog", "cat"} else None
        update_sensors({"pet_detected": pet, "timestamp": now_ms()})
        publish_sensor_update()
        run_auto_logic(load_data()["sensors"])


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