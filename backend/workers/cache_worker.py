import asyncio
import json
import aio_pika
from services.cache import invalidate_cache, store_in_cache, init_cache
from services.embedding import load_model
from core.config import settings

async def main():
    load_model()
    await init_cache()

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("cache_queue", durable=True)
    fanout = await channel.declare_exchange("cache_invalidation", aio_pika.ExchangeType.FANOUT)
    invalidation_queue = await channel.declare_queue("", exclusive=True)
    await invalidation_queue.bind(fanout)
    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(
                message.body.decode()
            )
            await store_in_cache(body["text"], body["response"], body["embedding"],  body.get("system_prompt"), body["model"], body["temperature"])
            print(body)
    async def fanout_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(
                message.body.decode()
            )
            await invalidate_cache(body["id"])
            print(body)
    await queue.consume(on_message)
    await invalidation_queue.consume(fanout_message)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
