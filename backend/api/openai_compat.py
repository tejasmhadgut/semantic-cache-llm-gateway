from fastapi import APIRouter, Depends
from schemas.openai import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, Message
from core.auth import get_current_user
from core.rate_limiter import check_rate_limit
from services.embedding import get_embedding
from services.cache import search_cache
from services.llm import call_llm
from services.queue import publish_cache_write
from core.deduplicator import deduplicate
from services.normalizer import normalize
from core.tracing import get_tracer
from core.metrics import cache_hits, cache_misses, llm_requests, active_requests, request_latency
import asyncio
import time
import uuid


router = APIRouter(prefix="/v1", tags=["openai-compat"])

SIMILARITY_THRESHOLD = 0.85

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, current_user: str = Depends(get_current_user)):
    tracer = get_tracer()
    await check_rate_limit(current_user)

    # extract system and user prompt from messages
    system_prompt = next((m.content for m in request.messages if m.role == "system"), None)
    user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), None)

    with request_latency.labels(method="POST", endpoint="/v1/chat/completions").time():
        active_requests.inc()
        try:
            with tracer.start_as_current_span("normalizing"):
                prompt = normalize(user_message)
            with tracer.start_as_current_span("embedding"):
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(None, get_embedding, prompt)
            with tracer.start_as_current_span("Search Cache"):
                results = await search_cache(prompt, embeddings, system_prompt, request.model, request.temperature)

            if results and float(results[0]["vector_distance"]) < (1 - SIMILARITY_THRESHOLD):
                cache_hits.labels(method="POST", endpoint="/v1/chat/completions").inc()
                response_text = results[0]["response"]
                cache_hit = True
            else:
                with tracer.start_as_current_span("Call LLM"):
                    response_text = await deduplicate(prompt, lambda: call_llm(prompt, system_prompt, request.model))
                cache_misses.labels(method="POST", endpoint="/v1/chat/completions").inc()
                llm_requests.labels(method="POST", endpoint="/v1/chat/completions").inc()
                await publish_cache_write(prompt, response_text, embeddings, system_prompt, request.model, request.temperature)
                cache_hit = False
        finally:
            active_requests.dec()

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        object="chat.completion",
        created=int(time.time()),
        model=request.model,
        choices=[ChatCompletionChoice(
            index=0,
            message=Message(role="assistant", content=response_text),
            finish_reason="stop"
        )],
        cache_hit=cache_hit
    )
    