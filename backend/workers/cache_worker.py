import asyncio
import json
import aio_pika
from services.cache import store_in_cache, init_cache
from services.embedding import load_model
from core.config import settings

async def main():
    load_model()
    await init_cache()

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("cache_queue", durable=True)

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(
                message.body.decode()
            )
            store_in_cache(body["text"], body["response"], body["embedding"])
            print(body)
    
    await queue.consume(on_message)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
