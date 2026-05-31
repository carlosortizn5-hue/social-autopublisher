import redis
import logging
from app.config import settings

logger = logging.getLogger(__name__)

r = redis.from_url(settings.redis_url)


def acquire_lock(key: str, timeout: int = 300) -> bool:
    """Try to acquire a distributed lock"""
    return r.set(key, "1", nx=True, ex=timeout) is not None


def release_lock(key: str) -> bool:
    """Release a distributed lock"""
    return r.delete(key) > 0
