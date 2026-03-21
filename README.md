# 🚀 Đồ Án Đa Ngành


## 🌟 Hardware

## 🌟 Gateway
- **Auto-Detect Port:** Tự động tìm và kết nối với bo mạch (Yolo:Bit/Arduino) qua cổng USB, không cần hardcode tên cổng.
- **Data Buffering & Anti-Noise:** Bộ lọc thông minh giúp chống nhiễu, chống mất gói tin khi truyền nhận Serial.
- **Smart Routing:** Phân loại và định tuyến lệnh điều khiển từ Server xuống đúng thiết bị phần cứng (Bơm, LED, Servo).

## 🌟 BackEnd


## 🌟 FrontEnd
- Chịu trách nhiệm hiển thị UI Dashboard giám sát và điều khiển.
- Công nghệ: ReactJS, Vite.
* **Hướng dẫn chạy Frontend:**
    **1. Mở terminal, di chuyển vào thư mục frontend: `cd frontend`**
    **2. Cài đặt thư viện: `npm install`**
    **3. Khởi chạy giao diện: `npm run dev`**

---

## 🛠️ Hướng Dẫn Cài Đặt

**1. Clone code về máy:**
```bash
git clone <link_github_của_bạn>
git fetch
git checkout nhánh_của_mình (hardware/backend/frontend/gateway)
```
*Lưu ý Sau khi code xong lưu và đẩy lên nhánh của mình*
```bash

git push origin nhánh_của_mình (hardware/backend/frontend/gateway)
```


**2. Cài đặt thư viện:**
Dự án sử dụng file `requirements.txt` để quản lý thư viện. Bạn chỉ cần mở Terminal/CMD tại thư mục chứa code và gõ 1 lệnh duy nhất sau:
```bash
pip install -r requirements.txt
```


