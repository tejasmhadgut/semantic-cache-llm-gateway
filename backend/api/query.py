from fastapi import APIRouter, Depends
from core.deduplicator import deduplicate
from services.queue import publish_cache_write
from core.auth import get_current_user
from services.embedding import get_embedding
from services.cache import search_cache
from services.llm import call_llm
from services.normalizer import normalize
from core.rate_limiter import check_rate_limit
from schemas.query import QueryRequest
router = APIRouter(prefix="/query", tags=["query"])

SIMILARITY_THRESHOLD = 0.85

@router.post("/")
async def query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    await check_rate_limit(current_user)
    prompt = normalize(request.prompt)
    embeddings = get_embedding(prompt)
    system_prompt = request.system_prompt
    model = request.model
    temperature = request.temperature
    results = await search_cache(prompt, embeddings, system_prompt, model, temperature)
    if results and float(results[0]["vector_distance"]) <(1 - SIMILARITY_THRESHOLD):
        return {"prompt":prompt,"response": results[0]["response"],"cache_hit":True}
    else:
        response = await deduplicate(prompt, lambda: call_llm(prompt, system_prompt, model))
        await publish_cache_write(prompt, response, embeddings, system_prompt, model, temperature)
        return {"prompt":prompt,"response":response,"cache_hit":False}
    