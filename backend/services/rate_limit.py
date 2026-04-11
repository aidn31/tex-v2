import os
import random
import time

import redis

RATE_LIMITS = {
    "gemini-2.5-pro": 3,      # requests per 60 seconds — update when quota increases
    "gemini-2.5-flash": 15,   # requests per 60 seconds
    "gemini-file-api": 10,    # file uploads per 60 seconds — separate from model rate limits
}


def _get_redis_client():
    return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))


def acquire_gemini_slot(model: str, redis_client=None):
    """Acquire a rate limit slot for a Gemini API call.

    Blocks until a slot is available. Uses a Redis-based token bucket
    shared across all workers and Cloud Run instances.
    """
    if redis_client is None:
        redis_client = _get_redis_client()

    key = f"rate_limit:{model}"
    limit = RATE_LIMITS.get(model)
    if limit is None:
        raise ValueError(f"Unknown model for rate limiting: {model}")

    while True:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)
        if count <= limit:
            return
        time.sleep(2 + random.uniform(0, 1))
