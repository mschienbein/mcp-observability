from __future__ import annotations
import os
import time
import threading
from typing import Optional, Dict


class TraceIndexBase:
    def set(self, session_id: str, trace_id: str) -> None:  # pragma: no cover
        raise NotImplementedError
    def get(self, session_id: Optional[str]) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError


class InMemoryTraceIndex(TraceIndexBase):
    """session_id -> {trace_id, ts} (thread-safe, per-process)"""
    def __init__(self) -> None:
        self._d: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()
    def set(self, session_id: str, trace_id: str) -> None:
        with self._lock:
            self._d[session_id] = {"trace_id": trace_id, "ts": time.time()}
    def get(self, session_id: Optional[str]) -> Optional[str]:
        if not session_id:
            return None
        with self._lock:
            rec = self._d.get(session_id)
            return rec["trace_id"] if rec else None


class RedisTraceIndex(TraceIndexBase):
    """Redis-backed session_id -> trace_id mapping (cross-process)."""
    def __init__(self, url: Optional[str] = None, prefix: str = "mcp:trace_index:", ttl_seconds: int = 60 * 60 * 24) -> None:
        try:
            import redis  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("RedisTraceIndex requires 'redis' package installed") from e
        self._redis = redis.from_url(url or os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        self._prefix = prefix
        self._ttl = ttl_seconds
    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"
    def set(self, session_id: str, trace_id: str) -> None:
        k = self._key(session_id)
        # Store both id and timestamp
        self._redis.hset(k, mapping={"trace_id": trace_id, "ts": str(time.time())})
        self._redis.expire(k, self._ttl)
    def get(self, session_id: Optional[str]) -> Optional[str]:
        if not session_id:
            return None
        k = self._key(session_id)
        return self._redis.hget(k, "trace_id")


def get_trace_index() -> TraceIndexBase:
    backend = (os.getenv("TRACE_INDEX_BACKEND", "memory").strip().lower())
    if backend == "redis":
        try:
            return RedisTraceIndex()
        except Exception:
            # Fallback to memory if Redis is unavailable/misconfigured
            return InMemoryTraceIndex()
    return InMemoryTraceIndex()
