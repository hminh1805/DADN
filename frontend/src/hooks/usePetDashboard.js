import { useState, useEffect, useCallback, useRef } from "react";
import { fetchLatestSensor, fetchDeviceStatus, fetchActivities, sendCommand, setMode } from "../services/api";
import { initSocket, SOCKET_EVENTS } from "../services/socket";
import { MOCK_SENSOR, MOCK_DEVICES } from "../constants/types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

export function usePetDashboard() {
  // ── Trạng thái cảm biến ─────────────────────────────────────
  const [temp,       setTemp]       = useState(MOCK_SENSOR.temperature);
  const [humidity,   setHumidity]   = useState(MOCK_SENSOR.humidity);
  const [dogFood,    setDogFood]    = useState(MOCK_SENSOR.dog_food);
  const [catFood,    setCatFood]    = useState(MOCK_SENSOR.cat_food);
  const [water,      setWater]      = useState(MOCK_SENSOR.water_level);

  // ── Trạng thái thiết bị ────────────────────────────────────
  const [fanOn,      setFanOn]      = useState(MOCK_DEVICES.fan);
  const [heaterOn,   setHeaterOn]   = useState(MOCK_DEVICES.heater);
  const [pumpOn,     setPumpOn]     = useState(MOCK_DEVICES.pump);
  const [speakerOn,  setSpeakerOn]  = useState(MOCK_DEVICES.speaker);
  const [detected,   setDetected]   = useState(null);
  const [motion,     setMotion]     = useState(false);

  // ── Trạng thái UI ──────────────────────────────────────────
  const [connected,  setConnected]  = useState(USE_MOCK);
  const [autoMode,   setAutoMode]   = useState(true);
  const [activities, setActivities] = useState([]);
  const [chartData,  setChartData]  = useState([]);

  const tempRef     = useRef(temp);
  const humidityRef = useRef(humidity);
  useEffect(() => { tempRef.current = temp; },     [temp]);
  useEffect(() => { humidityRef.current = humidity; }, [humidity]);
  //
  useEffect(() => {
    if (USE_MOCK) return;
    setMode(autoMode ? "auto" : "manual").catch(console.error);
  }, [autoMode]);

  // ── Helper thêm activity ───────────────────────────────────
  const addActivity = useCallback((type, message) => {
    setActivities(prev => [
      { id: Date.now().toString(), type, message, timestamp: Date.now() },
      ...prev.slice(0, 9),
    ]);
  }, []);

  // ── Áp dữ liệu cảm biến từ API/socket vào state ─────────────
  const applySensor = useCallback((data) => {
    setTemp(+data.temperature);
    setHumidity(+data.humidity);
    setDogFood(+data.dog_food);
    setCatFood(+data.cat_food);
    setWater(+data.water_level);
    const t2 = new Date(data.timestamp ?? Date.now());
    const ts = `${t2.getHours()}:${String(t2.getMinutes()).padStart(2,"0")}`;
    setChartData(prev => [
      ...prev.slice(-5),
      { time: ts, temp: Math.round(+data.temperature), hum: Math.round(+data.humidity) },
    ]);
  }, []);

  // ── Áp trạng thái thiết bị ─────────────────────────────────
  const applyDevices = useCallback((data) => {
    if (data.fan      !== undefined) setFanOn(data.fan);
    if (data.heater   !== undefined) setHeaterOn(data.heater);
    if (data.pump     !== undefined) setPumpOn(data.pump);
    if (data.speaker  !== undefined) setSpeakerOn(data.speaker);
    if (data.dog_feeder !== undefined || data.cat_feeder !== undefined) {
      setDetected(data.dog_feeder ? "dog" : data.cat_feeder ? "cat" : null);
    }
  }, []);

  // ── Khởi tạo: fetch lần đầu + kết nối socket ───────────────
  useEffect(() => {
    // Fetch dữ liệu khởi tạo
    fetchLatestSensor().then(applySensor).catch(console.error);
    fetchDeviceStatus().then(applyDevices).catch(console.error);
    fetchActivities().then(list =>
      setActivities(list.map(a => ({ ...a })))
    ).catch(console.error);

    if (USE_MOCK) {
      // ── Giả lập realtime khi chưa có backend ─────────────
      const id = setInterval(() => {
        const t = clamp(tempRef.current + (Math.random() - 0.5) * 1.5, 20, 36);
        const h = clamp(humidityRef.current + (Math.random() - 0.5) * 3, 40, 85);
        applySensor({
          temperature: +t.toFixed(1),
          humidity: Math.round(h),
          dog_food: 0,   // giữ nguyên, chỉ update cảm biến môi trường
          cat_food: 0,
          water_level: 0,
          timestamp: Date.now(),
        });
        setMotion(Math.random() > 0.88);
        const r = Math.random();
        setDetected(r > 0.65 ? (Math.random() > 0.5 ? "dog" : "cat") : r < 0.3 ? null : (p => p));
      }, 3000);
      return () => clearInterval(id);
    }

    // ── Kết nối socket thật ──────────────────────────────────
    const sock = initSocket();
    if (!sock) return;

    sock.on("connect",    () => setConnected(true));
    sock.on("disconnect", () => setConnected(false));

    // Backend emit "sensor_update" → cập nhật cảm biến
    sock.on(SOCKET_EVENTS.SENSOR_UPDATE, applySensor);

    // Backend emit "device_status" → cập nhật thiết bị
    sock.on(SOCKET_EVENTS.DEVICE_STATUS, applyDevices);

    // Backend emit "pet_detected" → cập nhật nhận diện
    sock.on(SOCKET_EVENTS.PET_DETECTED, ({ pet }) => setDetected(pet ?? null));

    // Backend emit "alert" → thêm vào activity
    sock.on(SOCKET_EVENTS.ALERT, (alert) => {
      addActivity(alert.type, alert.message);
    });

    return () => {
      sock.off(SOCKET_EVENTS.SENSOR_UPDATE);
      sock.off(SOCKET_EVENTS.DEVICE_STATUS);
      sock.off(SOCKET_EVENTS.PET_DETECTED);
      sock.off(SOCKET_EVENTS.ALERT);
    };
  }, [applySensor, applyDevices, addActivity]);

  // ── Auto mode logic (chạy ở client khi mock, hoặc để backend xử lý) ──
  useEffect(() => {
    if (!autoMode || !USE_MOCK) return;
    setFanOn(temp > 30);
    setHeaterOn(temp < 22);
  }, [autoMode, temp]);

  // ── Gửi lệnh thủ công ─────────────────────────────────────
  const dispatchCommand = useCallback(async (device, action, optimisticFn) => {
    // Cập nhật UI ngay lập tức (optimistic update)
    optimisticFn?.();
    try {
      const res = await sendCommand({ device, action });
      if (res.success) {
        addActivity("success", `Lệnh "${action}" → ${device} thành công`);
      }
    } catch (err) {
      addActivity("error", `Lỗi gửi lệnh đến ${device}: ${err.message}`);
      // TODO: rollback optimistic nếu cần
    }
  }, [addActivity]);

  const feedDog = () => dispatchCommand(
    "dog_feeder", "dispense",
    () => { setDogFood(p => clamp(p + 15, 0, 100)); addActivity("success", "Đã nhả thức ăn cho Buddy"); }
  );

  const feedCat = () => dispatchCommand(
    "cat_feeder", "dispense",
    () => { setCatFood(p => clamp(p + 15, 0, 100)); addActivity("success", "Đã nhả thức ăn cho Mochi"); }
  );

  const refillWater = () => dispatchCommand(
    "pump", "refill",
    () => { setWater(p => clamp(p + 20, 0, 100)); addActivity("success", "Đã bơm nước"); }
  );

  const toggleDevice = (device, currentState) => dispatchCommand(
    device, currentState ? "off" : "on",
    () => {
      const setters = { fan: setFanOn, heater: setHeaterOn, pump: setPumpOn, speaker: setSpeakerOn };
      setters[device]?.(!currentState);
    }
  );

  return {
    // Cảm biến
    temp, humidity, dogFood, catFood, water,
    // Thiết bị
    fanOn, heaterOn, pumpOn, speakerOn,
    // Nhận diện
    detected, motion,
    // Kết nối
    connected,
    // Chế độ
    autoMode, setAutoMode,
    // Lịch sử
    activities, chartData,
    // Actions
    feedDog, feedCat, refillWater,
    toggleDevice,
    addActivity,
  };
}


