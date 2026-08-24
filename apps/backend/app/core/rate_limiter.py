import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request, HTTPException


class RateLimiter:
    """In-memory sliding window rate limiter. Use for auth endpoints.

    For production with multiple replicas, replace with Redis.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._store: Dict[str, Deque[float]] = defaultdict(deque)

    def _key(self, request: Request) -> str:
        # Prefer X-Forwarded-For, fallback to client host
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    def check(self, request: Request) -> None:
        now = time.monotonic()
        key = self._key(request)
        q = self._store[key]
        # purge expired
        while q and q[0] <= now - self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        q.append(now)


# Default limiters
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 10/min per IP for login/signup
strict_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5/min for sensitive
upload_limiter = RateLimiter(max_requests=20, window_seconds=60)
