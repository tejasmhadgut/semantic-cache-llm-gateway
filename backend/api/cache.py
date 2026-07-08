from fastapi import APIRouter, Depends
from core.auth import get_current_user
from services.cache import build_cache_key
from services.queue import publish_invalidation
from schemas.query import QueryRequest


router = APIRouter(prefix="/cache", tags=["cache"])

@router.delete("/invalidate")
async def invalidate(request: QueryRequest, current_user: str = Depends(get_current_user)):
    cache_key = build_cache_key(request.prompt, request.system_prompt, request.model, request.temperature)
    await publish_invalidation(cache_key)
    return {"invalidated": cache_key}
