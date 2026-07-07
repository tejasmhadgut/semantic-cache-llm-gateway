import time
from fastapi import HTTPException
from core.config import settings
from redis.asyncio import Redis

client = Redis.from_url(settings.REDIS_URL)

async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    now = time.time()
    window_start = now - settings.RATE_LIMIT_WINDOW
    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    _, count = await pipe.execute()
    if count >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Request Rate Limited, Try again in sometime")
    else:
        pipe = client.pipeline()
        pipe.zadd(key, {str(now):now})
        pipe.expire(key, settings.RATE_LIMIT_WINDOW)
        await pipe.execute()
    


