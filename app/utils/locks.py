import redis
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url)
        except Exception as e:
            logger.warning(f"Redis connection failed, locks will be disabled: {e}")
            return None
    return _redis_client


def acquire_lock(key: str, timeout: int = 300) -> bool:
    """Try to acquire a distributed lock (returns True even if Redis unavailable)"""
    r = get_redis()
    if not r:
        return True
    try:
        return r.set(key, "1", nx=True, ex=timeout) is not None
    except Exception as e:
        logger.warning(f"Lock acquire failed, proceeding: {e}")
        return True


def release_lock(key: str) -> bool:
    """Release a distributed lock"""
    r = get_redis()
    if not r:
        return True
    try:
        return r.delete(key) > 0
    except Exception as e:
        logger.warning(f"Lock release failed: {e}")
        return True
