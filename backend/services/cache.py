import time
import logging
from services.redis_client import get_client, get_read_client
from redisvl.query import VectorQuery
from core.config import settings
from redisvl.index import AsyncSearchIndex
from core.circuit_breaker import redis_breaker, RedisUnavailableError
import numpy as np
import hashlib

schema = {
    "index": {"name": "documents"},
    "fields": [
        {"name": "text", "type": "text"},
        {"name": "embedding", "type": "vector", "attrs": {"dims": 384, "distance_metric": "cosine", "algorithm": "hnsw"}},
        {"name": "response", "type": "text"},
        {"name": "timestamp", "type": "numeric"},
        {"name": "hit_count", "type": "numeric"}
    ]
}

index = AsyncSearchIndex.from_dict(schema)
read_index = AsyncSearchIndex.from_dict(schema)

def build_cache_key(prompt: str, system_prompt: str = None, model: str = "llama3.2", temperature: float = 0.7) -> str:
    key_parts = f"{prompt}|{system_prompt or ''}|{model}|{temperature}"
    return hashlib.sha256(key_parts.encode()).hexdigest()

async def init_cache():
    await index.set_client(get_client())
    await read_index.set_client(get_read_client())
    await index.create(overwrite=False)

async def search_cache(text: str, embeddings: list[float], system_prompt: str = None, model: str = "llama3.2", temperature: float = 0.7):
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    vector_query = VectorQuery(
        vector=embedding_bytes,
        vector_field_name="embedding",
        num_results=1,
        return_fields=["text", "response"]
    )
    try:
        return await redis_breaker.call(read_index.query(vector_query))
    except RedisUnavailableError:
        logging.warning("Redis unavailable — cache search skipped, falling through to LLM")
        return None

async def store_in_cache(text: str, response: str, embeddings: list[float], system_prompt: str = None, model: str = "llama3.2", temperature: float = 0.7):
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    cacheKey = build_cache_key(text, system_prompt, model, temperature)
    try:
        await redis_breaker.call(index.load(
            [{"text": text, "embedding": embedding_bytes, "response": response, "timestamp": time.time(), "hit_count": 0}],
            keys=[f"rvl:{cacheKey}"]
        ))
        await redis_breaker.call(get_client().expire(f"rvl:{cacheKey}", settings.CACHE_TTL_SECONDS))
    except RedisUnavailableError:
        logging.warning("Redis unavailable — cache write skipped")

async def invalidate_cache(cacheKey: str):
    try:
        await redis_breaker.call(get_client().delete(f"rvl:{cacheKey}"))
    except RedisUnavailableError:
        logging.warning("Redis unavailable — cache invalidation skipped")
