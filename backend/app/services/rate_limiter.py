import math
import time
from collections import deque
from typing import Protocol

from fastapi import HTTPException, Request, status

from app.config import settings


class RateLimiter(Protocol):
    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        ...

    def reset(self) -> None:
        ...


class InMemorySlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter for auth and flag submission endpoints."""

    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = {}

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = deque()
            self._buckets[key] = bucket

        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, math.ceil(bucket[0] + window_seconds - now))
            return False, retry_after

        bucket.append(now)
        return True, 0

    def reset(self) -> None:
        self._buckets.clear()


rate_limiter = InMemorySlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(scope: str, identifier: str, limit: int, window_seconds: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return

    allowed, retry_after = rate_limiter.check(f"{scope}:{identifier}", limit, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


async def rate_limit_auth(request: Request) -> None:
    enforce_rate_limit(
        scope=f"auth:{request.url.path}",
        identifier=get_client_ip(request),
        limit=settings.RATE_LIMIT_AUTH_MAX,
        window_seconds=settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
    )


async def rate_limit_flag_submit(request: Request) -> None:
    enforce_rate_limit(
        scope=f"flag:{request.url.path}",
        identifier=get_client_ip(request),
        limit=settings.RATE_LIMIT_FLAG_MAX,
        window_seconds=settings.RATE_LIMIT_FLAG_WINDOW_SECONDS,
    )
