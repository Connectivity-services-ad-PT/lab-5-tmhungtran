import asyncio
import json
import logging
import signal
from typing import Dict, Any

import aio_pika

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [notify-worker] %(message)s",
)
logger = logging.getLogger(__name__)

async def handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False, ignore_processed=True):
        try:
            body = message.body.decode("utf-8")
            payload: Dict[str, Any] = json.loads(body)
            
            recipient = payload.get("recipient", "unknown-recipient")
            title = payload.get("title", "Không có tiêu đề")

            # Giả lập xử lý gửi SMS/Email
            logger.info("Đã gửi thông báo thành công tới %s | title=%s", recipient, title)
            
            await message.ack()
        except Exception as e:
            # Thêm tracking retries thủ công thông qua headers
            headers = message.headers or {}
            retries = headers.get("x-retries", 0)
            
            if retries < settings.MAX_RETRIES:
                logger.warning("Xử lý thất bại (lần %d). Requeue message...", retries + 1)
                new_headers = headers.copy()
                new_headers["x-retries"] = retries + 1
                
                # Publish lại với header mới
                channel = message.channel
                new_message = aio_pika.Message(
                    body=message.body,
                    headers=new_headers,
                    delivery_mode=message.delivery_mode,
                    content_type=message.content_type,
                )
                await channel.default_exchange.publish(
                    new_message,
                    routing_key=settings.RABBITMQ_QUEUE,
                )
                await message.ack() # Ack message cũ vì đã publish bản mới có tăng retry
            else:
                logger.error("Đã vượt quá số lần retry (%d). Chuyển sang DLX.", settings.MAX_RETRIES)
                # Bằng cách reject với requeue=False, message sẽ tự động bay sang DLX vì queue đã cài đặt x-dead-letter-exchange
                await message.reject(requeue=False)

async def start_worker() -> None:
    logger.info("Đang kết nối RabbitMQ...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Cấu hình Dead Letter Exchange và Dead Letter Queue
        dlx_exchange = await channel.declare_exchange(settings.RABBITMQ_DLX, aio_pika.ExchangeType.DIRECT, durable=True)
        dead_queue = await channel.declare_queue(settings.RABBITMQ_DEAD_QUEUE, durable=True)
        await dead_queue.bind(dlx_exchange, routing_key=settings.RABBITMQ_QUEUE)

        # Cấu hình Queue chính với DLX
        queue_arguments = {
            "x-dead-letter-exchange": settings.RABBITMQ_DLX,
            "x-dead-letter-routing-key": settings.RABBITMQ_QUEUE,
        }
        main_queue = await channel.declare_queue(
            settings.RABBITMQ_QUEUE, 
            durable=True, 
            arguments=queue_arguments
        )

        logger.info("Worker đã sẵn sàng lắng nghe queue '%s'", settings.RABBITMQ_QUEUE)
        
        # Bắt đầu consume
        await main_queue.consume(handle_message)
        
        try:
            # Chạy vô hạn cho tới khi bị hủy
            await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("Đang dừng Worker an toàn (Graceful Shutdown)...")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    main_task = loop.create_task(start_worker())
    
    # Lắng nghe các tín hiệu ngắt từ hệ điều hành / Docker (SIGINT, SIGTERM)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, main_task.cancel)
    
    try:
        loop.run_until_complete(main_task)
    finally:
        logger.info("Worker đã thoát hoàn toàn.")
