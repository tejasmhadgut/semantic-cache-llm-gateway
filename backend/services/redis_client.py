from redis.asyncio.sentinel import Sentinel
from core.config import settings

_sentinel = None
_client = None
_read_client = None

def init_redis():
    global _sentinel, _client, _read_client
    hosts = [(h.split(':')[0], int(h.split(':')[1])) for h in settings.SENTINEL_HOSTS.split(',')]
    _sentinel = Sentinel(hosts, socket_timeout=0.5)
    _client = _sentinel.master_for(settings.REDIS_MASTER_NAME, socket_timeout=0.5)
    _read_client = _sentinel.slave_for(settings.REDIS_MASTER_NAME, socket_timeout=0.5)

def get_client():
    return _client

def get_read_client():
    return _read_client
