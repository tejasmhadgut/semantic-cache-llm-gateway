from fastapi import APIRouter, Depends
from core.auth import get_current_user
from services.cache import build_cache_key
from services.queue import publish_invalidation
from schemas.query import QueryRequest
from db.database import get_db
from models.near_miss import NearMiss
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/cache", tags=["cache"])

@router.delete("/invalidate")
async def invalidate(request: QueryRequest, current_user: str = Depends(get_current_user)):
    cache_key = build_cache_key(request.prompt, request.system_prompt, request.model, request.temperature)
    await publish_invalidation(cache_key)
    return {"invalidated": cache_key}

@router.get("/near-misses")
async def near_misses(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    result = await db.execute(select(NearMiss).order_by(NearMiss.timestamp.desc()).limit(50))
    rows = result.scalars().all()
    return [{"prompt": r.prompt, "top_distance": r.top_distance, "timestamp": r.timestamp} for r in rows]

@router.get("/threshold-analysis")
async def threshold_analysis(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    result = await db.execute(select(NearMiss))
    rows = result.scalars().all()

    thresholds = [round(0.10 + i * 0.02, 2) for i in range(14)]

    analysis = []
    for t in thresholds:
        hits_at_threshold = sum(1 for r in rows if r.top_distance < t)
        analysis.append({
            "threshold_distance": t,
            "similarity_threshold": round(1 - t, 2),
            "near_misses_converted": hits_at_threshold
        })

    return {
        "current_threshold_distance": 0.15,
        "current_similarity_threshold": 0.85,
        "total_near_misses_analyzed": len(rows),
        "analysis": analysis
    }
