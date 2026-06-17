# RUN_COMPOSE.md - Hướng dẫn chạy Lab 05

**Người thực hiện:** Sinh viên Trần Mạnh Hùng  
**MSSV:** 1771020313  
**Lớp:** CNTT17-10  
**Vai trò:** team-notify - Smart Campus Operations Platform

Tài liệu này mô tả các bước khởi chạy Notification API, Worker Service và RabbitMQ bằng Docker Compose.

## 1. Chuẩn bị môi trường

Yêu cầu cài đặt:

- Docker Engine hoặc Docker Desktop
- Docker Compose v2
- Make, nếu muốn dùng các lệnh tắt trong `Makefile`

Tạo file môi trường local từ file mẫu:

```bash
cp .env.example .env
```

File `.env.example` chỉ chứa dummy data phục vụ thực hành. Không đưa secret thật vào file này.

## 2. Khởi chạy stack

Chạy bằng Docker Compose:

```bash
docker compose up -d --build
```

Hoặc dùng Makefile:

```bash
make compose-up
```

Stack gồm 3 service:

- `team-notify-rabbitmq`: RabbitMQ broker và management UI.
- `team-notify-api`: FastAPI service nhận request `/notify`.
- `team-notify-worker`: Worker tiêu thụ message từ queue `notifications`.

## 3. Kiểm tra trạng thái

Xem danh sách container:

```bash
docker compose ps
```

Kiểm tra API healthcheck:

```bash
curl http://localhost:8000/health
```

Kết quả kỳ vọng:

```json
{"status":"ok","service":"notify-api"}
```

RabbitMQ Management UI có thể truy cập tại:

```text
http://localhost:15672
```

Thông tin đăng nhập mặc định lấy từ `.env`:

- Username: `notify_user`
- Password: `notify_pass_123`

## 4. Gửi thử thông báo

Gửi request vào API:

```bash
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{"title":"Cảnh báo phòng học","message":"Nhiệt độ phòng A101 vượt ngưỡng cho phép.","recipient":"student@example.com"}'
```

Kết quả kỳ vọng:

```json
{"status":"queued","message":"Thông báo đã được đưa vào hàng đợi xử lý."}
```

Sau đó xem log worker:

```bash
docker compose logs -f notify-worker
```

Log kỳ vọng có dạng:

```text
Đã gửi thông báo thành công tới student@example.com
```

## 5. Dừng stack

Dừng container:

```bash
docker compose down
```

Hoặc:

```bash
make compose-down
```

Nếu cần xóa cả volume dữ liệu RabbitMQ:

```bash
docker compose down -v
```

## 6. Lệnh nhanh

```bash
make compose-up
make logs
make compose-down
```

## 7. Ghi chú vận hành

- RabbitMQ dùng volume `rabbitmq-data` để lưu dữ liệu bền vững.
- Cả ba service cùng nằm trong custom bridge network `team-internal`.
- `notify-api` và `notify-worker` chỉ khởi động sau khi `rabbitmq` đạt trạng thái healthy.
- Image được tag theo quy ước `v0.1.0-team-notify`.
