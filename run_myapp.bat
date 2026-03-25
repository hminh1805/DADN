@echo off
echo ===================================================
echo     KHOI DONG HE THONG CHAM SOC THU CUNG 
echo ===================================================

echo [1] Dang mo Backend Server...
:: start cmd /k mở một cửa sổ terminal mới
:: cd backend: Chui vào thư mục backend
:: call venv\Scripts\activate: Bật môi trường ảo ảo
:: python run.py: Nổ máy Server
start cmd /k ".\venv\Scripts\activate && cd backend && python run.py"

echo [2] Dang mo Gateway USB...

start cmd /k ".\venv\Scripts\activate && cd gatewayV1 && python gatewayv1.py"

echo [3] Dang mo Frontend Web...
:: (Tui giả sử thư mục FE của sếp tên là frontend)
start cmd /k "cd frontend && npm run dev"

echo.
