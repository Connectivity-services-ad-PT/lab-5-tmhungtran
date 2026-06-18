import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

import aio_pika
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [notify-api] %(message)s",
)
logger = logging.getLogger(__name__)

class NotificationPayload(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=120)]
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    recipient: Annotated[str, Field(min_length=1, max_length=120)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo kết nối RabbitMQ một lần duy nhất lúc startup
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await connection.channel()
        queue_arguments = {
            "x-dead-letter-exchange": settings.RABBITMQ_DLX,
            "x-dead-letter-routing-key": settings.RABBITMQ_QUEUE,
        }
        await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True, arguments=queue_arguments)
        
        app.state.rabbitmq_connection = connection
        app.state.rabbitmq_channel = channel
        logger.info("Đã kết nối thành công tới RabbitMQ.")
    except Exception:
        logger.exception("Không thể kết nối tới RabbitMQ lúc startup.")
        raise
        
    yield
    
    # Đóng kết nối khi tắt app
    if hasattr(app.state, "rabbitmq_connection"):
        await app.state.rabbitmq_connection.close()
        logger.info("Đã đóng kết nối RabbitMQ an toàn.")

app = FastAPI(
    title="Smart Campus Notification API",
    version="0.1.0",
    description="API nhận thông báo và publish vào RabbitMQ queue (Asynchronous).",
    lifespan=lifespan
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "OK", "service": "notify-api"}

@app.get("/partner/health")
async def call_partner() -> dict[str, str]:
    url = f"{settings.PARTNER_SERVICE_URL}/health"
    logger.info("Đang gọi API đối tác tại: %s", url)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                partner_data = response.json()
                return {
                    "status": "OK",
                    "partner_url": url,
                    "partner_response": partner_data.get("status", "Unknown")
                }
            else:
                logger.warning("API đối tác trả về mã trạng thái: %d", response.status_code)
                raise HTTPException(status_code=503, detail="Service phụ thuộc timeout/lỗi")
    except Exception as exc:
        logger.error("Lỗi/timeout khi gọi API đối tác: %s", str(exc))
        raise HTTPException(status_code=503, detail="Service phụ thuộc timeout/lỗi")

@app.post("/notify", status_code=202)
async def notify(payload: NotificationPayload, request: Request) -> dict[str, str]:
    try:
        channel: aio_pika.abc.AbstractChannel = request.app.state.rabbitmq_channel
        
        message_body = payload.model_dump()
        message_body["created_at"] = int(time.time())
        
        message = aio_pika.Message(
            body=json.dumps(message_body, ensure_ascii=False).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        
        await channel.default_exchange.publish(
            message,
            routing_key=settings.RABBITMQ_QUEUE,
        )
        logger.info("Đã publish thông báo vào queue '%s' cho recipient=%s", settings.RABBITMQ_QUEUE, payload.recipient)
        
    except Exception as exc:
        logger.exception("Lỗi khi publish thông báo vào RabbitMQ")
        raise HTTPException(status_code=503, detail="RabbitMQ is not available") from exc

    return {
        "status": "queued",
        "message": "Thông báo đã được đưa vào hàng đợi xử lý.",
    }
