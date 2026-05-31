import redis
import logging
from app.config import settings

logger = logging.getLogger(__name__)

r = redis.from_url(settings.redis_url)


def check_rate_limit(key: str, max_calls: int, window: int = 3600) -> bool:
    """Check if rate limit exceeded (key, max_calls per window in seconds)"""
    current = r.incr(key)
    if current == 1:
        r.expire(key, window)
    return current <= max_calls
