from prometheus_client import (Counter, Gauge, Histogram)


cache_hits = Counter(
    "cache_hit_total",
    "Total Cache Hit",
    ["method","endpoint"]
)

cache_misses = Counter(
    "cache_misses_total",
    "Total Cache misses",
    ["method","endpoint"]
)

llm_requests = Counter(
    "llm_requests_total",
    "Total LLM Requests",
    ["method","endpoint"]
)

active_requests = Gauge(
    "active_requests",
    "Number of active requests"
)
request_latency = Histogram(
    "http_request_duration_seconds",
    "Http request latency",
    ["method","endpoint"],
    buckets=[0.05,0.1,0.25,0.5,1.0,2.5,5.0,10.0,30.0]
)
