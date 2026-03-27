import copy
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
MAX_ACTIVITIES = 10

DEFAULT_DATA = {
    "mode": "auto",
    "sensors": {
        "temperature": 0.0,
        "humidity": 0.0,
        "water_level": 0.0,
        "dog_food": 0.0,
        "cat_food": 0.0,
        "motion": False,
        "pet_detected": None,
        "timestamp": 0,
    },
    "devices": {
        "fan": False,
        "heater": False,
        "pump": False,
        "speaker": False,
        "pet_feeder": False,
        "servo": False,
    },
    "activities": [],
}


def now_ms():
    return int(datetime.utcnow().timestamp() * 1000)


def deep_merge(base, incoming):
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def ensure_file():
    if not os.path.exists(DATA_FILE):
        save_data(copy.deepcopy(DEFAULT_DATA))


def load_data():
    ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        incoming = json.load(f)

    merged = copy.deepcopy(DEFAULT_DATA)
    deep_merge(merged, incoming)
    merged["sensors"].pop("distance", None)
    return merged


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_sensors(sensor_payload):
    data = load_data()
    data["sensors"].update(sensor_payload)
    data["sensors"]["timestamp"] = sensor_payload.get("timestamp", now_ms())
    save_data(data)


def update_device(device_name, status):
    data = load_data()
    data["devices"][device_name] = bool(status)
    save_data(data)


def set_mode(mode):
    data = load_data()
    data["mode"] = mode
    save_data(data)


def add_activity(activity_type, message):
    data = load_data()
    data["activities"].insert(
        0,
        {
            "id": str(now_ms()),
            "type": activity_type,
            "message": message,
            "timestamp": now_ms(),
        },
    )
    data["activities"] = data["activities"][:MAX_ACTIVITIES]
    save_data(data)
