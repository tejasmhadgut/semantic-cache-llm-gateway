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
similarity_scores = Histogram(
    "similarity_score",
    "Vector distance of top cache result per query",
    buckets=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0]
)

queue_depth = Gauge("queue_depth",
                     "Number of messages ready in cache_queue"
)

queue_consumers = Gauge("queue_consumers",
                         "Number of active consumers on cache_queue"
)
