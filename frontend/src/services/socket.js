/**
 * socket.js  —  Kết nối WebSocket (socket.io)
 * ─────────────────────────────────────────────
 * Backend cần chạy socket.io và emit đúng các event trong SOCKET_EVENTS
 */

import { io } from "socket.io-client";
import { SOCKET_URL, SOCKET_EVENTS } from "../constants/config";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

let socket = null;

/**
 * Khởi tạo kết nối socket (gọi 1 lần khi app mount)
 * @returns {import("socket.io-client").Socket | null}
 */
export function initSocket() {
  if (USE_MOCK) return null;
  if (socket) return socket;

  socket = io(SOCKET_URL, {
    reconnectionAttempts: 5,
    reconnectionDelay: 2000,
    transports: ["websocket"],
  });

  socket.on("connect",         () => console.log("[Socket] Connected:", socket.id));
  socket.on("disconnect",      () => console.log("[Socket] Disconnected"));
  socket.on("connect_error",   (e) => console.error("[Socket] Error:", e.message));

  return socket;
}

export function getSocket() { return socket; }

/**
 * Gửi lệnh qua socket (thay thế cho REST nếu backend dùng socket cho command)
 * @param {import("../constants/types").CommandPayload} payload
 */
export function emitCommand(payload) {
  if (!socket?.connected) {
    console.warn("[Socket] Chưa kết nối, không gửi được lệnh");
    return;
  }
  socket.emit(SOCKET_EVENTS.COMMAND, payload);
}

export { SOCKET_EVENTS };
