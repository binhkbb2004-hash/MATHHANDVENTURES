# Sử dụng một ảnh nền Python chính thức
FROM python:3.11-slim

# Đặt thư mục làm việc bên trong container
WORKDIR /app

# Cài đặt thư viện hệ thống cho OpenCV (sử dụng tên gói khác)
RUN apt-get update
RUN apt-get install -y libgl1

# Sao chép các file yêu cầu và cài đặt thư viện Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của dự án vào container
COPY . .

# Ra lệnh cho container chạy ứng dụng khi khởi động
CMD gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:$PORT