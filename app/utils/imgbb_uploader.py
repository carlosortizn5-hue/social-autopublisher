import base64
import logging
import requests
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


def upload_image(image_bytes: bytes, public_id: str) -> Optional[str]:
    """
    Upload raw image bytes to imgbb.
    Returns the hosted URL string, or None on error.

    Intended to be called via `asyncio.to_thread(upload_image, bytes, id)`
    from async publishers so the blocking HTTP call doesn't block the event loop.
    """
    if not image_bytes:
        logger.warning("upload_image called with empty bytes")
        return None

    if not settings.imgbb_api_key:
        logger.warning("imgbb_api_key not configured — cannot upload image")
        return None

    try:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        response = requests.post(
            IMGBB_UPLOAD_URL,
            data={
                "key": settings.imgbb_api_key,
                "image": encoded,
                "name": public_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        url: str = response.json()["data"]["url"]
        logger.debug(f"imgbb upload OK: {url}")
        return url
    except Exception as e:
        logger.error(f"imgbb upload failed for public_id={public_id}: {e}")
        return None
