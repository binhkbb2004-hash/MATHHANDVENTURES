# Sử dụng một ảnh nền Python chính thức
FROM python:3.11-slim

# Đặt thư mục làm việc bên trong container
WORKDIR /app

# --- Cài đặt một bộ đầy đủ các thư viện hệ thống cần thiết cho OpenCV ---
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# Sao chép các file yêu cầu và cài đặt thư viện Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của dự án vào container
COPY . .

# Ra lệnh cho container chạy ứng dụng khi khởi động
CMD gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:$PORT