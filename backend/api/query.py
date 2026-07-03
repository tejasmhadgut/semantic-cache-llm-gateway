from fastapi import APIRouter, Depends
from services.queue import publish_cache_write
from core.auth import get_current_user
from services.embedding import get_embedding
from services.cache import search_cache
from services.llm import call_llm
from services.normalizer import normalize

router = APIRouter(prefix="/query", tags=["query"])

SIMILARITY_THRESHOLD = 0.85

@router.post("/")
async def query(prompt: str, current_user: str = Depends(get_current_user)):
    prompt = normalize(prompt)
    embeddings = get_embedding(prompt)
    results = await search_cache(embeddings)
    if results and float(results[0]["vector_distance"]) <(1 - SIMILARITY_THRESHOLD):
        return {"prompt":prompt,"response": results[0]["response"],"cache_hit":True}
    else:
        response = await call_llm(prompt)
        await publish_cache_write(prompt, response, embeddings)
        return {"prompt":prompt,"response":response,"cache_hit":False}
    