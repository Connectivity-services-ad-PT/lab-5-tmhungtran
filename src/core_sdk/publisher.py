import asyncio
import json
import logging
import time
from typing import Dict, Any

import aio_pika

logger = logging.getLogger("notify-sdk")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [notify-sdk] %(message)s'))
logger.addHandler(handler)

class NotificationClient:
    """
    SDK dành cho Core Team để đẩy thẳng message vào RabbitMQ của Team Notify.
    Không cần đi qua HTTP API.
    """
    def __init__(self, amqp_url: str = "amqp://notify_user:notify_pass_123@localhost:5672/"):
        self.amqp_url = amqp_url
        self.queue_name = "notifications"
        self._connection = None
        self._channel = None

    async def connect(self):
        """Khởi tạo kết nối tới RabbitMQ. Core Team nên gọi hàm này lúc startup."""
        self._connection = await aio_pika.connect_robust(self.amqp_url)
        self._channel = await self._connection.channel()
        logger.info("Đã kết nối thành công tới RabbitMQ Broker của Team Notify.")

    async def close(self):
        """Đóng kết nối."""
        if self._connection:
            await self._connection.close()
            logger.info("Đã đóng kết nối an toàn.")

    async def send_notification(self, title: str, message_content: str, recipient: str):
        """Hàm publish message dành cho các service của Core Team."""
        if not self._channel:
            raise RuntimeError("Chưa khởi tạo kết nối. Hãy gọi await connect() trước.")

        payload: Dict[str, Any] = {
            "title": title,
            "message": message_content,
            "recipient": recipient,
            "created_at": int(time.time()),
            "source": "core_service_direct"
        }

        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=self.queue_name,
        )
        logger.info("Đã đẩy thẳng thông báo cho %s vào queue '%s'.", recipient, self.queue_name)


# ==========================================
# VÍ DỤ SỬ DỤNG DÀNH CHO CORE TEAM
# ==========================================
async def main():
    # 1. Team Core khởi tạo client kết nối tới hệ thống của Team Notify
    # (Nếu Core chạy trong docker, truyền vào amqp://notify_user:notify_pass_123@rabbitmq:5672/)
    client = NotificationClient(amqp_url="amqp://notify_user:notify_pass_123@localhost:5672/")
    
    # 2. Mở kết nối
    await client.connect()

    # 3. Gửi thông báo trực tiếp
    await client.send_notification(
        title="[Core] Cảnh báo hệ thống",
        message_content="Phát hiện sinh viên đăng nhập hệ thống nội bộ từ IP lạ.",
        recipient="security@smartcampus.edu.vn"
    )

    # 4. Đóng kết nối
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
