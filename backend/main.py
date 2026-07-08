from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from api.auth import router as auth_router
from services.cache import init_cache
from services.embedding import load_model
from core.auth import get_current_user
from api.query import router as query_router
from services.queue import connect_queue
from api.cache import router as cache_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    await init_cache()
    await connect_queue()
    yield

app = FastAPI(title="Semantic Cache LLM gateway", lifespan=lifespan)

    
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(cache_router)
@app.get("/health")
async def health():
    return {"status":"ok"}

@app.get("/protected")
async def protected(current_user: str = Depends(get_current_user)):
    return {"message":f"Hello {current_user}"}