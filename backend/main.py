from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
import prometheus_client
from api.auth import router as auth_router
from services.cache import init_cache
from services.embedding import load_model
from core.auth import get_current_user
from api.query import router as query_router
from services.queue import connect_queue
from api.cache import router as cache_router
from core.tracing_middleware import TracingMiddleware
import asyncio
import httpx
from core.metrics import queue_depth, queue_consumers

async def poll_queue_metrics():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://rabbitmq:15672/api/queues/%2F/cache_queue",
                    auth=("guest", "guest"),
                    timeout=5.0
                )
                data = resp.json()
                queue_depth.set(data.get("messages_ready", 0))
                queue_consumers.set(data.get("consumers", 0))
        except Exception:
            pass
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    await init_cache()
    await connect_queue()
    asyncio.create_task(poll_queue_metrics())
    yield

app = FastAPI(title="Semantic Cache LLM gateway", lifespan=lifespan)

app.add_middleware(TracingMiddleware)
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(cache_router)
@app.get("/health")
async def health():
    return {"status":"ok"}

@app.get("/metrics")
async def metrics():
    return Response(
        prometheus_client.generate_latest(),
        media_type=prometheus_client.CONTENT_TYPE_LATEST
    )
@app.get("/protected")
async def protected(current_user: str = Depends(get_current_user)):
    return {"message":f"Hello {current_user}"}