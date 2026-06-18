# HƯỚNG DẪN CẤP NHẬT CẤU HÌNH VÀ TÍCH HỢP LIÊN NHÓM (BUỔI 6)

Tài liệu này hướng dẫn cách xác định địa chỉ IP máy cá nhân khi kết nối mạng LAN Hotspot (iPhone/Android hotspot) và cấu hình biến môi trường trước khi chạy hệ thống.

---

## 1. Xác định địa chỉ IP trên máy tính (Windows)

Khi kết nối máy tính vào mạng Hotspot di động dùng chung trên lớp, bạn cần lấy địa chỉ IP của máy mình để cung cấp cho các nhóm đối tác.

1. Mở terminal (**Command Prompt** hoặc **PowerShell**).
2. Chạy lệnh sau:
   ```cmd
   ipconfig
   ```
3. Tìm đến card mạng không dây đang kết nối (thường tên là `Wireless LAN adapter Wi-Fi`).
4. Tìm dòng `IPv4 Address`. Địa chỉ này thường có định dạng `172.20.10.x` (đối với iPhone Hotspot) hoặc `192.168.x.x`.
5. Đây chính là địa chỉ IP của bạn trong mạng LAN nội bộ. Hãy gửi IP này cho nhóm đối tác để họ cấu hình gọi sang API của bạn.

---

## 2. Cấu hình biến môi trường (`.env`)

Trước khi khởi chạy Docker Compose, bạn cần cập nhật file `.env` chứa IP của nhóm đối tác mà bạn muốn kết nối tới:

1. Mở file `.env` ở thư mục gốc của dự án.
2. Tìm khóa cấu hình `PARTNER_SERVICE_URL`.
3. Thay thế giá trị bằng địa chỉ IP thực tế của đối tác:
   ```env
   # Ví dụ: IP của nhóm đối tác Core/Camera là 172.20.10.5
   PARTNER_SERVICE_URL=http://172.20.10.5:8000
   ```
4. Lưu file.

---

## 3. Khởi chạy hệ thống

Do có sự thay đổi trong dependencies (`requirements.txt`), bạn cần build lại image để đảm bảo thư viện `httpx` được cài đặt đầy đủ:

```bash
# Build lại và khởi động các service ở chế độ background
docker compose up -d --build
```

---

## 4. Kiểm tra tích hợp

Sau khi hệ thống khởi động thành công:
- **Kiểm tra Healthcheck của bản thân:** Truy cập `http://localhost:8000/health` (hoặc `http://<IP_CỦA_BẠN>:8000/health` từ máy khác) phải trả về `{"status": "OK", "service": "notify-api"}`.
- **Kiểm tra Tích hợp đối tác:** Truy cập `http://localhost:8000/partner/health`. API sẽ gọi sang API đối tác qua địa chỉ IP đã cấu hình:
  - Nếu đối tác hoạt động ổn định: Trả về trạng thái `OK` kèm phản hồi từ đối tác.
  - Nếu kết nối tới đối tác bị timeout (sau 3 giây) hoặc lỗi mạng: API lập tức trả về mã lỗi HTTP `503 Service Unavailable` kèm thông báo chi tiết `"Service phụ thuộc timeout/lỗi"`, không làm treo ứng dụng.
