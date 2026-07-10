from db.database import get_db
from models.near_miss import NearMiss
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from core.deduplicator import deduplicate
from services.queue import publish_cache_write
from core.auth import get_current_user
from services.embedding import get_embedding
from services.cache import search_cache
from services.llm import call_llm
from services.normalizer import normalize
from core.rate_limiter import check_rate_limit
from schemas.query import QueryRequest
from core.tracing import get_tracer
from core.metrics import cache_hits, cache_misses, llm_requests, active_requests, request_latency, similarity_scores


router = APIRouter(prefix="/query", tags=["query"])

SIMILARITY_THRESHOLD = 0.85
NEAR_MISS_MARGIN = 0.20

@router.post("/")
async def query(request: QueryRequest, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tracer = get_tracer()
    with tracer.start_as_current_span("rate_limiting"):
        await check_rate_limit(current_user)
    with request_latency.labels(method="POST", endpoint="/query/").time():
        active_requests.inc()
        try:
            with tracer.start_as_current_span("normalizing"):
                prompt = normalize(request.prompt)
            with tracer.start_as_current_span("embedding"):
                embeddings = get_embedding(prompt)
            system_prompt = request.system_prompt
            model = request.model
            temperature = request.temperature
            with tracer.start_as_current_span("Search Cache"):
                results = await search_cache(prompt, embeddings, system_prompt, model, temperature)
            if results:
                similarity_scores.observe(float(results[0]["vector_distance"]))
            if results and float(results[0]["vector_distance"]) <(1 - SIMILARITY_THRESHOLD):
                cache_hits.labels(method="POST", endpoint="/query/").inc()
                return {"prompt":prompt,"response": results[0]["response"],"cache_hit":True}
            else:
                with tracer.start_as_current_span("Call LLM"):
                    response = await deduplicate(prompt, lambda: call_llm(prompt, system_prompt, model))
                cache_misses.labels(method="POST", endpoint="/query/").inc()
                if results and float(results[0]["vector_distance"]) < (1 - SIMILARITY_THRESHOLD) + NEAR_MISS_MARGIN:
                    near_miss = NearMiss(prompt=prompt, top_distance=float(results[0]["vector_distance"]), timestamp=datetime.now(timezone.utc))
                    db.add(near_miss)
                    await db.commit()
                llm_requests.labels(method="POST", endpoint="/query/").inc()
                with tracer.start_as_current_span("publish to Cache"):
                    await publish_cache_write(prompt, response, embeddings, system_prompt, model, temperature)
                return {"prompt":prompt,"response":response,"cache_hit":False}
        finally:
            active_requests.dec()
