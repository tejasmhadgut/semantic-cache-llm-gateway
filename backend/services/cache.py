
from redisvl.query import VectorQuery
from core.config import settings
from redisvl.index import AsyncSearchIndex
from redis.asyncio import Redis
import numpy as np

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
        }
    ]
    }
index = AsyncSearchIndex.from_dict(
        schema
    )


async def init_cache():
    await index.connect(settings.REDIS_URL)
    await index.create(overwrite=False)

async def search_cache(embeddings: list[float]) -> list[float]:
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    
    vector_query = VectorQuery(
        vector = embedding_bytes,
        vector_field_name="embedding",
        num_results=1,
        return_fields=["text", "response"]
    )
    results = await index.query(vector_query)
    return results

async def store_in_cache(text: str,response:str, embeddings: list[float]):
    embedding_bytes = np.array(embeddings, dtype=np.float32).tobytes()
    await index.load([
        {
            "text": text,
            "embedding": embedding_bytes,
            "response":response
        }
        
    ])
