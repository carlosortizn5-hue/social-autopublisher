import httpx
import logging
from app.publishers.base import Publisher
from app.models import Product
from app.config import settings

logger = logging.getLogger(__name__)


class FacebookPublisher(Publisher):
    async def publish(self, product: Product, caption: str) -> tuple[bool, str]:
        if not settings.meta_long_lived_token or not settings.fb_page_id:
            return False, "Facebook credentials not configured"

        try:
            async with httpx.AsyncClient() as client:
                url = f"https://graph.instagram.com/v18.0/{settings.fb_page_id}/feed"
                data = {
                    "message": caption,
                    "access_token": settings.meta_long_lived_token,
                }
                if product.image_url:
                    data["link"] = product.link

                response = await client.post(url, data=data)
                response.raise_for_status()
                post_id = response.json().get("id")
                return True, f"Facebook post {post_id} published"

        except Exception as e:
            logger.error(f"Error publishing to Facebook: {e}")
            return False, str(e)


class InstagramPublisher(Publisher):
    async def publish(self, product: Product, caption: str) -> tuple[bool, str]:
        return False, "Instagram publishing not yet implemented"
