# 🚀 Smart IoT Gateway (Python) - Đồ Án DADN

Đây là mã nguồn Gateway (Trạm trung chuyển dữ liệu) viết bằng Python, đóng vai trò là "trái tim" kết nối giữa **Phần cứng (Mạch vi điều khiển)** và **Hệ thống Server/Web (Đám mây)**.

Hệ thống sử dụng giao thức **MQTT** kết nối với Adafruit IO và giao tiếp **Serial (Cổng USB)** với bo mạch.

## 🌟 Tính Năng Nổi Bật
- **Auto-Detect Port:** Tự động tìm và kết nối với bo mạch (Yolo:Bit/Arduino) qua cổng USB, không cần hardcode tên cổng.
- **Data Buffering & Anti-Noise:** Bộ lọc thông minh giúp chống nhiễu, chống mất gói tin khi truyền nhận Serial.
- **Smart Routing:** Phân loại và định tuyến lệnh điều khiển từ Server xuống đúng thiết bị phần cứng (Bơm, LED, Servo).
- **Hybrid Mode (Mạch thật & Giả lập):** Rút cáp USB ra tự động chuyển sang chế độ Mocking Data (Giả lập dữ liệu ảo) để team Web/Backend thoải mái test API mà không cần chờ phần cứng.

---

## 🛠️ Hướng Dẫn Cài Đặt (Cho Team Lập Trình)

**1. Clone code về máy:**
```bash
git clone <link_github_của_bạn>
cd <tên_thư_mục>

**2. Cài đặt thư viện:**
Dự án sử dụng file `requirements.txt` để quản lý thư viện. Bạn chỉ cần mở Terminal/CMD tại thư mục chứa code và gõ 1 lệnh duy nhất sau:
```bash
pip install -r requirements.txt



