
/**
 * @typedef {Object} SensorPayload
 * Socket event: "sensor_update"  |  GET /api/sensors/latest
 *
 * @property {number} temperature   - Nhiệt độ (°C), vd: 28.5
 * @property {number} humidity      - Độ ẩm (%), vd: 65
 * @property {number} dog_food      - Thức ăn chó (%), 0–100
 * @property {number} cat_food      - Thức ăn mèo (%), 0–100
 * @property {number} water_level   - Mực nước (%), 0–100
 * @property {number} timestamp     - Unix ms, vd: Date.now()
 */

/**
 * @typedef {Object} DeviceStatusPayload
 * Socket event: "device_status"  |  GET /api/devices/status
 *
 * @property {boolean} fan          - Quạt mini
 * @property {boolean} heater       - Đèn sưởi
 * @property {boolean} pump         - Máy bơm
 * @property {boolean} speaker      - Loa cảnh báo
 * @property {boolean} dog_feeder   - Máy ăn chó (true = đang mở)
 * @property {boolean} cat_feeder   - Máy ăn mèo (true = đang mở)
 */

/**
 * @typedef {Object} PetDetectedPayload
 * Socket event: "pet_detected"
 *
 * @property {"dog"|"cat"|null} pet  - Thú cưng được nhận diện
 * @property {number} confidence     - Độ chính xác 0–1, vd: 0.97
 * @property {number} timestamp      - Unix ms
 */

/**
 * @typedef {Object} AlertPayload
 * Socket event: "alert"
 *
 * @property {string} id                          - ID duy nhất
 * @property {"warning"|"error"|"info"} type
 * @property {string} title
 * @property {string} message
 * @property {number} timestamp                   - Unix ms
 */

/**
 * @typedef {Object} CommandPayload
 * POST /api/devices/command  (Frontend → Backend)
 *
 * @property {"fan"|"heater"|"pump"|"speaker"|"dog_feeder"|"cat_feeder"} device
 * @property {"on"|"off"|"dispense"|"refill"} action
 *
 * Ví dụ:  { device: "dog_feeder", action: "dispense" }
 *         { device: "fan",        action: "on"       }
 */

/**
 * @typedef {Object} CommandResponse
 * Response của POST /api/devices/command
 *
 * @property {boolean} success
 * @property {string}  message   - Mô tả kết quả
 */

/**
 * @typedef {Object} ActivityItem
 * GET /api/activities
 *
 * @property {string} id
 * @property {"success"|"info"|"warning"|"error"} type
 * @property {string} message
 * @property {number} timestamp   - Unix ms
 */

// ── Dữ liệu giả lập (dùng khi chưa có backend) ──────────────────
export const MOCK_SENSOR = {
  temperature: 28,
  humidity: 65,
  dog_food: 75,
  cat_food: 18,
  water_level: 72,
  timestamp: Date.now(),
};

export const MOCK_DEVICES = {
  fan: false,
  heater: false,
  pump: false,
  speaker: true,
  dog_feeder: false,
  cat_feeder: false,
};

export const MOCK_ACTIVITIES = [
  { id: "1", type: "success", message: "Buddy đã ăn đúng giờ (12:00)", timestamp: Date.now() - 7200000 },
  { id: "2", type: "info",    message: "Nước đã được refill tự động",  timestamp: Date.now() - 10800000 },
  { id: "3", type: "warning", message: "Nhiệt độ phòng vượt 27°C",    timestamp: Date.now() - 14400000 },
];
