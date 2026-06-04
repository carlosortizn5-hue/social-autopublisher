import asyncio
import httpx
import logging
import time
from app.publishers.base import Publisher
from app.models import Product
from app.config import settings
from app.utils.image_processor import enhance_product_image
from app.utils.imgbb_uploader import upload_image

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v18.0"


class FacebookPublisher(Publisher):
    async def publish(self, product: Product, caption: str) -> tuple[bool, str]:
        if not settings.meta_long_lived_token or not settings.fb_page_id:
            return False, "Facebook credentials not configured"

        try:
            async with httpx.AsyncClient() as client:
                url = f"{GRAPH_API_BASE}/{settings.fb_page_id}/feed"
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
        if not settings.meta_long_lived_token or not settings.ig_business_account_id:
            return False, "Instagram credentials not configured (meta_long_lived_token / ig_business_account_id)"

        # 1. Build enhanced image
        image_bytes = enhance_product_image(product)

        # 2. Upload to imgbb to get a publicly hosted URL
        hosted_url: str | None = None
        if image_bytes:
            public_id = f"product_{product.id}"
            hosted_url = await asyncio.to_thread(upload_image, image_bytes, public_id)

        # Fallback: use raw image_url if enhanced image or upload failed
        if not hosted_url:
            hosted_url = product.image_url
            if not hosted_url:
                return False, "No image URL available for Instagram post"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Step A: Create media container
                container_url = f"{GRAPH_API_BASE}/{settings.ig_business_account_id}/media"
                container_payload = {
                    "image_url": hosted_url,
                    "caption": caption,
                    "access_token": settings.meta_long_lived_token,
                }
                container_resp = await client.post(container_url, data=container_payload)
                container_resp.raise_for_status()
                creation_id = container_resp.json().get("id")
                if not creation_id:
                    return False, f"Instagram media container creation returned no id: {container_resp.text}"

                # Wait for media to be ready
                await asyncio.sleep(3)

                # Step B: Publish the container
                publish_url = f"{GRAPH_API_BASE}/{settings.ig_business_account_id}/media_publish"
                publish_payload = {
                    "creation_id": creation_id,
                    "access_token": settings.meta_long_lived_token,
                }
                publish_resp = await client.post(publish_url, data=publish_payload)
                publish_resp.raise_for_status()
                post_id = publish_resp.json().get("id")
                return True, f"Instagram post {post_id} published (media container {creation_id})"

        except httpx.HTTPStatusError as e:
            body = e.response.text
            logger.error(f"Instagram API HTTP error: {e.response.status_code} — {body}")
            return False, f"HTTP {e.response.status_code}: {body}"
        except Exception as e:
            logger.error(f"Error publishing to Instagram: {e}", exc_info=True)
            return False, str(e)
