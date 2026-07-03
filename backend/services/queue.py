import json
import aio_pika
from aio_pika import Message
from core.config import settings
connection = None
channel = None
async def connect_queue():
    global connection, channel
    connection = await aio_pika.connect_robust(
        settings.RABBITMQ_URL
    )
    channel = await connection.channel()
    queue = await channel.declare_queue(
        "cache_queue",
        durable=True
    )


async def publish_cache_write(text: str, response: str, embedding: list[float]):
    payload = {"text":text, "response":response, "embedding":embedding}
    await channel.default_exchange.publish(
        Message(
            body=json.dumps(payload).encode()
        ),
        routing_key="cache_queue"
    )