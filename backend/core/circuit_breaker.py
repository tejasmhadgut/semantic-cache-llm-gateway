import asyncio
import time

OPERATION_TIMEOUT = 0.5
_FAILURE_THRESHOLD = 3
_RECOVERY_TIMEOUT = 5.0

_CLOSED = "closed"
_OPEN = "open"
_HALF_OPEN = "half_open"


class RedisUnavailableError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold=_FAILURE_THRESHOLD, recovery_timeout=_RECOVERY_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at = None
        self._state = _CLOSED
        self._probe_in_flight = False

    @property
    def state(self):
        if self._state == _OPEN and time.monotonic() - self._opened_at >= self.recovery_timeout:
            self._state = _HALF_OPEN
        return self._state

    async def call(self, coro):
        s = self.state
        if s == _OPEN:
            raise RedisUnavailableError("Circuit open")
        if s == _HALF_OPEN:
            if self._probe_in_flight:
                raise RedisUnavailableError("Circuit half-open — probe in flight")
            self._probe_in_flight = True
        try:
            result = await asyncio.wait_for(coro, timeout=OPERATION_TIMEOUT)
            self._on_success()
            return result
        except Exception as e:
            self._probe_in_flight = False
            self._on_failure()
            raise RedisUnavailableError(str(e)) from e

    def _on_success(self):
        self._failures = 0
        self._state = _CLOSED
        self._probe_in_flight = False

    def _on_failure(self):
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = _OPEN
            self._opened_at = time.monotonic()


redis_breaker = CircuitBreaker()
