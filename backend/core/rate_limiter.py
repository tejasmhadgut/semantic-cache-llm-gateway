import time
import logging
from fastapi import HTTPException
from core.config import settings
from services.redis_client import get_client
from core.circuit_breaker import redis_breaker, RedisUnavailableError

async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    now = time.time()
    window_start = now - settings.RATE_LIMIT_WINDOW
    try:
        pipe = get_client().pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        _, count = await redis_breaker.call(pipe.execute())
        if count >= settings.RATE_LIMIT_REQUESTS:
            raise HTTPException(status_code=429, detail="Request Rate Limited, Try again in sometime")
        pipe = get_client().pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, settings.RATE_LIMIT_WINDOW)
        await redis_breaker.call(pipe.execute())
    except RedisUnavailableError:
        logging.warning("Redis unavailable — rate limiter skipped, failing open")
