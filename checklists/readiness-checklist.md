# Readiness Checklist - Lab 05 team-notify

Checklist xác nhận trạng thái sẵn sàng của hệ thống Notification API, Worker Service và RabbitMQ trong Smart Campus Operations Platform.

- [x] **RabbitMQ khởi động thành công:** service `rabbitmq` chạy bằng image official `rabbitmq:3.13-management`, có healthcheck `rabbitmq-diagnostics check_port_connectivity`.
- [x] **Worker sẵn sàng:** service `notify-worker` kết nối RabbitMQ và liên tục lắng nghe queue `notifications`.
- [x] **API kết nối queue tốt:** endpoint `POST /notify` validate JSON payload và publish message vào RabbitMQ queue thay vì gửi trực tiếp.
- [x] **Biến môi trường tách biệt:** cấu hình được đặt trong `.env.example` và được Docker Compose đọc qua `env_file` cùng biến môi trường.
- [x] **Network team-internal hoạt động:** các service `rabbitmq`, `notify-api` và `notify-worker` cùng tham gia custom bridge network `team-internal`.
- [x] **Image tuân thủ quy ước tag version:** image sử dụng tag `v0.1.0-team-notify`, ví dụ `smart-campus/notify-api:v0.1.0-team-notify` và `smart-campus/notify-worker:v0.1.0-team-notify`.
