/**
 * api.js  —  Tầng gọi REST API
 * ────────────────────────────────────────────
 * Tất cả HTTP request đều đi qua đây.
 * Khi backend thay đổi URL / auth → chỉ sửa file này.
 */

import axios from "axios";
import { API_URL, ENDPOINTS } from "../constants/config";
import { MOCK_SENSOR, MOCK_DEVICES, MOCK_ACTIVITIES } from "../constants/types";

// Bật mock khi chưa có backend (đổi thành false khi backend sẵn sàng)
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

const http = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: { "Content-Type": "application/json" },
});

// ── Interceptor: log lỗi ra console ────────────────────────────
http.interceptors.response.use(
  res => res,
  err => {
    console.error("[API Error]", err.config?.url, err.message);
    return Promise.reject(err);
  }
);

// ── Sensor ─────────────────────────────────────────────────────
/**
 * Lấy dữ liệu cảm biến mới nhất
 * @returns {Promise<import("../constants/types").SensorPayload>}
 */
export async function fetchLatestSensor() {
  if (USE_MOCK) {
    // Giả lập thay đổi nhỏ
    return {
      ...MOCK_SENSOR,
      temperature: +(MOCK_SENSOR.temperature + (Math.random() - 0.5) * 2).toFixed(1),
      humidity: Math.round(MOCK_SENSOR.humidity + (Math.random() - 0.5) * 4),
      timestamp: Date.now(),
    };
  }
  const { data } = await http.get(ENDPOINTS.SENSOR_LATEST);
  return data;
}

// ── Devices ────────────────────────────────────────────────────
/**
 * Lấy trạng thái tất cả thiết bị
 * @returns {Promise<import("../constants/types").DeviceStatusPayload>}
 */
export async function fetchDeviceStatus() {
  if (USE_MOCK) return { ...MOCK_DEVICES };
  const { data } = await http.get(ENDPOINTS.DEVICE_STATUS);
  return data;
}

/**
 * Gửi lệnh điều khiển thiết bị
 * @param {import("../constants/types").CommandPayload} payload
 * @returns {Promise<import("../constants/types").CommandResponse>}
 */
export async function sendCommand(payload) {
  if (USE_MOCK) {
    console.log("[MOCK] Command sent:", payload);
    return { success: true, message: "Mock: lệnh đã gửi" };
  }
  const { data } = await http.post(ENDPOINTS.COMMAND, payload);
  return data;
}

// ── Activities ─────────────────────────────────────────────────
/**
 * Lấy lịch sử hoạt động
 * @returns {Promise<import("../constants/types").ActivityItem[]>}
 */
export async function fetchActivities() {
  if (USE_MOCK) return [...MOCK_ACTIVITIES];
  const { data } = await http.get(ENDPOINTS.ACTIVITIES);
  return data;
}

export async function setMode(mode) {
  if (USE_MOCK) return { success: true, message: "Mock: đã đổi mode" };
  const { data } = await http.post(ENDPOINTS.MODE, { mode });
  return data;
}