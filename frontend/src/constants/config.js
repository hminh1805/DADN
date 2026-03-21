export const API_URL    = import.meta.env.VITE_API_URL    ?? "http://localhost:3000";
export const SOCKET_URL = import.meta.env.VITE_SOCKET_URL ?? "http://localhost:3000";

/** Tên các event socket.io — backend phải emit đúng tên này */
export const SOCKET_EVENTS = {
  // Backend → Frontend
  SENSOR_UPDATE:  "sensor_update",   // dữ liệu cảm biến realtime
  ALERT:          "alert",           // cảnh báo đột xuất
  DEVICE_STATUS:  "device_status",   // trạng thái thiết bị thay đổi
  PET_DETECTED:   "pet_detected",    // nhận diện thú cưng

  // Frontend → Backend
  COMMAND:        "command",         // gửi lệnh điều khiển thủ công
};

/** Tên các REST endpoint — backend phải tạo đúng path này */
export const ENDPOINTS = {
  SENSOR_LATEST:  "/api/sensors/latest",   // GET  → SensorPayload
  DEVICE_STATUS:  "/api/devices/status",   // GET  → DeviceStatusPayload
  COMMAND:        "/api/devices/command",  // POST → CommandPayload
  ACTIVITIES:     "/api/activities",       // GET  → ActivityItem[]
};
