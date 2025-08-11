from typing import Any, Optional
import os
import json

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


async def init_redis(app) -> None:
    if redis is None:
        app.state.redis = None
        return
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(url, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        app.state.redis = None
        return
    app.state.redis = client


async def close_redis(app) -> None:
    client = getattr(app.state, "redis", None)
    if client is not None:
        try:
            await client.aclose()
        except Exception:
            pass


async def get_cache(app, key: str) -> Optional[Any]:
    client = getattr(app.state, "redis", None)
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def set_cache(app, key: str, value: Any, ttl_seconds: int = 300) -> None:
    client = getattr(app.state, "redis", None)
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        return


def build_cache_key(prefix: str, **parts: Any) -> str:
    stable = ":".join(f"{k}={parts[k]}" for k in sorted(parts.keys()))
    return f"{prefix}:{stable}"


