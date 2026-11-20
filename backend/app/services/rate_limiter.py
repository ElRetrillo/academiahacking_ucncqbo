import math
import time
from collections import OrderedDict, deque
from typing import Protocol

from fastapi import HTTPException, Request, status

from app.config import settings


class RateLimiter(Protocol):
    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        ...

    def reset(self) -> None:
        ...


class InMemorySlidingWindowRateLimiter:
    """Bounded-memory sliding-window rate limiter for auth and flag submission endpoints."""

    def __init__(self, max_keys: int = 10_000) -> None:
        self._max_keys = max(1, max_keys)
        self._buckets: OrderedDict[str, deque[float]] = OrderedDict()
        self._windows: dict[str, int] = {}

    def _prune_expired(self, now: float, window_seconds: int) -> None:
        for existing_key, bucket in list(self._buckets.items()):
            ttl = self._windows.get(existing_key, window_seconds)
            cutoff = now - ttl
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                self._buckets.pop(existing_key, None)
                self._windows.pop(existing_key, None)

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = self._buckets.get(key)

        if bucket is None:
            if len(self._buckets) >= self._max_keys:
                self._prune_expired(now, window_seconds)
            while len(self._buckets) >= self._max_keys:
                oldest_key, _ = self._buckets.popitem(last=False)
                self._windows.pop(oldest_key, None)
            bucket = deque()
            self._buckets[key] = bucket
        else:
            self._buckets.move_to_end(key)

        self._windows[key] = window_seconds

        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, math.ceil(bucket[0] + window_seconds - now))
            return False, retry_after

        bucket.append(now)
        return True, 0

    def reset(self) -> None:
        self._buckets.clear()
        self._windows.clear()


rate_limiter = InMemorySlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    trusted_proxies = settings.TRUSTED_PROXY_COUNT
    if trusted_proxies > 0:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            ips = [part.strip() for part in forwarded_for.split(",") if part.strip()]
            if ips:
                idx = -trusted_proxies if len(ips) >= trusted_proxies else 0
                return ips[idx]
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
