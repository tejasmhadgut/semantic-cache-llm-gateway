import json
import aio_pika
from aio_pika import Message
from core.config import settings
connection = None
channel = None
fanoutExchange = None
async def connect_queue():
    global connection, channel, fanoutExchange
    
    connection = await aio_pika.connect_robust(
        settings.RABBITMQ_URL
    )
    channel = await connection.channel()
    queue = await channel.declare_queue(
        "cache_queue",
        durable=True
    )
    fanoutExchange = await channel.declare_exchange(
        "cache_invalidation",
        aio_pika.ExchangeType.FANOUT
    )


async def publish_cache_write(text: str, response: str, embedding: list[float], system_prompt: str = None, model: str = None, temperature: float = 0.7):
    payload = {"text":text, "response":response, "embedding":embedding, "system_prompt": system_prompt, "model": model, "temperature": temperature}
    await channel.default_exchange.publish(
        Message(body=json.dumps(payload).encode()),
        routing_key="cache_queue"
    )



async def publish_invalidation(cache_key: str):
    payload = {"id":cache_key}
    await fanoutExchange.publish(
        Message(body=json.dumps(payload).encode()),
        routing_key=""
    )