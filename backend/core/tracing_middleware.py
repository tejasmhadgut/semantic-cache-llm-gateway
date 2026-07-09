from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.tracing import get_tracer

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tracer = get_tracer()
        span_name = f"{request.method} {request.url.path}"
        with tracer.start_as_current_span(span_name):
            response = await call_next(request)
            return response
