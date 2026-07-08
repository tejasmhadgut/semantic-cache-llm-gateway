
import time

from redisvl.query import VectorQuery
from core.config import settings
from redisvl.index import AsyncSearchIndex
from redis.asyncio import Redis
import numpy as np
import hashlib

client = Redis.from_url(settings.REDIS_URL)

schema={
        "index":{
            "name":"documents"
        },
        "fields": [
        {
            "name":"text",
            "type":"text"
        },
        {
            "name":"embedding",
            "type":"vector",
            "attrs":{
                    "dims":384,
                    "distance_metric":"cosine",
                    "algorithm":"hnsw"
                }
        },
        {
            "name":"response",
            "type":"text"
        },
        {
            "name": "timestamp",
            "type": "numeric"
        },
        {
            "name": "hit_count",
            "type": "numeric"
        }

    ]
    }
index = AsyncSearchIndex.from_dict(
        schema
    )

def build_cache_key(prompt: str, system_prompt: str= None, model: str = "llama3.2", temperature: float = 0.7) -> str:
    key_parts = f"{prompt}|{system_prompt or ''}|{model}|{temperature}"
    return hashlib.sha256(key_parts.encode()).hexdigest()

async def init_cache():
    await index.connect(settings.REDIS_URL)
    await index.create(overwrite=False)

async def search_cache(text: str, embeddings: list[float], system_prompt: str = None, model:str = "llama3.2", temperature: float = 0.7) -> list[float]:
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    vector_query = VectorQuery(
        vector = embedding_bytes,
        vector_field_name="embedding",
        num_results=1,
        return_fields=["text", "response"]
    )
    results = await index.query(vector_query)
    return results

async def store_in_cache(text: str,response:str, embeddings: list[float],system_prompt: str = None, model:str = "llama3.2", temperature: float = 0.7):
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    cacheKey = build_cache_key(text, system_prompt, model, temperature)
    await index.load([
        {
            
            "text": text,
            "embedding": embedding_bytes,
            "response":response,
            "timestamp": time.time(),
            "hit_count":0
        }
        
        
    ],
    keys=[f"rvl:{cacheKey}"]
    )
    await client.expire(f"rvl:{cacheKey}", settings.CACHE_TTL_SECONDS)

async def invalidate_cache(cacheKey: str):
    await client.delete(f"rvl:{cacheKey}")