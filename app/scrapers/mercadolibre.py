import httpx
import logging
from typing import List
from app.scrapers.base import Scraper, ScrapedProduct
from app.config import settings

logger = logging.getLogger(__name__)


class MercadoLibreScraper(Scraper):
    BASE_URL = "https://api.mercadolibre.com"

    async def scrape(self) -> List[ScrapedProduct]:
        if not settings.ml_client_id or not settings.ml_refresh_token:
            logger.warning("Mercado Libre credentials not configured")
            return []

        try:
            access_token = await self._get_access_token()
            if not access_token:
                return []
            products = await self._search_products(access_token)
            return products
        except Exception as e:
            logger.error(f"Error scraping Mercado Libre: {e}")
            return []

    async def _get_access_token(self) -> str | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/oauth/token",
                    data={
                        "grant_type": "refresh_token",
                        "client_id": settings.ml_client_id,
                        "client_secret": settings.ml_client_secret,
                        "refresh_token": settings.ml_refresh_token,
                    },
                )
                response.raise_for_status()
                return response.json().get("access_token")
        except Exception as e:
            logger.error(f"Error getting ML access token: {e}")
            return None

    async def _search_products(self, access_token: str) -> List[ScrapedProduct]:
        products = []
        return products
