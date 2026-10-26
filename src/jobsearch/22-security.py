"""API-key check and a sliding-window rate limiter."""
from __future__ import annotations
import hmac, os, time
from collections import defaultdict, deque


class AuthError(Exception):
    pass


class RateLimitError(Exception):
    pass


def check_api_key(provided: str | None, expected: str | None = None) -> None:
    expected = expected if expected is not None else os.environ.get("JOBSEARCH_API_KEY", "")
    if not expected:
        raise AuthError("server has no JOBSEARCH_API_KEY set")
    if not provided or not hmac.compare_digest(provided, expected):
        raise AuthError("invalid API key")


class RateLimiter:
    def __init__(self, max_calls: int = 30, per_seconds: float = 60.0, clock=time.monotonic):
        self.max_calls, self.per, self.clock = max_calls, per_seconds, clock
        self._hits: dict[str, deque] = defaultdict(deque)

    def hit(self, key: str) -> None:
        now = self.clock()
        q = self._hits[key]
        while q and now - q[0] > self.per:
            q.popleft()
        if len(q) >= self.max_calls:
            raise RateLimitError(f"rate limit: {self.max_calls} calls per {self.per:.0f}s")
        q.append(now)
