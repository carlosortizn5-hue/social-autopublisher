import httpx
import logging
from typing import List, Optional
from app.scrapers.base import Scraper, ScrapedProduct
from app.config import settings

logger = logging.getLogger(__name__)

_SEARCH_FETCH_LIMIT = 20
_SEARCH_RETURN_LIMIT = 8
_PRICE_MIN = 100


class MercadoLibreScraper(Scraper):
    BASE_URL = "https://api.mercadolibre.com"

    async def scrape(self) -> List[ScrapedProduct]:
        if not settings.ml_client_id or not settings.ml_refresh_token:
            logger.warning("Mercado Libre credentials not configured")
            return []

        required_config = {
            "ML_SITE_ID": settings.ml_site_id,
            "ML_SEARCH_QUERY": settings.ml_search_query,
        }
        missing = [name for name, value in required_config.items() if not value]
        if missing:
            logger.error(
                "Mercado Libre scraper aborted: missing required config: %s",
                ", ".join(missing),
            )
            return []

        try:
            async with httpx.AsyncClient() as client:
                access_token = await self._get_access_token(client)
                if not access_token:
                    return []
                products = await self._search_products(client, access_token)
                return products
        except Exception as e:
            logger.error("Error scraping Mercado Libre: %s", e)
            return []

    async def _get_access_token(self, client: httpx.AsyncClient) -> Optional[str]:
        """Exchange refresh_token for a short-lived access_token via ML OAuth."""
        try:
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
            logger.error("Error getting ML access token: %s", e)
            return None

    async def _build_affiliate_link(
        self, item_id: str, permalink: str, access_token: str, client: httpx.AsyncClient
    ) -> str:
        """Build an affiliate short_url via the ML Link Builder API.

        Args:
            item_id:      ML item identifier (e.g. "MLM123456789").
            permalink:    Direct item URL used as fallback.
            access_token: Valid OAuth access token.
            client:       Reusable httpx.AsyncClient for API calls.

        Returns:
            short_url from the Link Builder API, or a fallback permalink
            with affiliate tag appended when the API call fails.
        """
        try:
            payload = {
                "item_id": item_id,
                "channel": "affiliate",
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.post(
                f"{self.BASE_URL}/links/create",
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            if short_url := data.get("short_url"):
                return short_url
            logger.warning("Link Builder API returned no short_url for item %s; using fallback", item_id)
        except Exception as e:
            logger.warning(
                "Link Builder API failed for item %s: %s — using permalink fallback",
                item_id,
                e,
            )

        if settings.ml_affiliate_tag:
            return f"{permalink}?affiliate_id={settings.ml_affiliate_tag}"
        return permalink

    async def _search_products(self, client: httpx.AsyncClient, access_token: str) -> List[ScrapedProduct]:
        """Search ML catalog and return up to _SEARCH_RETURN_LIMIT products.

        Uses GET /sites/{site_id}/search with configurable query, a minimum
        price filter, and relevance sorting.  Each valid item gets an affiliate
        link built via _build_affiliate_link().

        Args:
            client:       Reusable httpx.AsyncClient for API calls.
            access_token: Valid OAuth access token.

        Returns:
            List of ScrapedProduct instances (up to _SEARCH_RETURN_LIMIT).
        """
        products: List[ScrapedProduct] = []
        try:
            params = {
                "q": settings.ml_search_query,
                "limit": _SEARCH_FETCH_LIMIT,
                "price": f"{_PRICE_MIN}-*",
                "sort": "relevance",
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(
                f"{self.BASE_URL}/sites/{settings.ml_site_id}/search",
                params=params,
                headers=headers,
                timeout=15.0,
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            for item in results:
                if len(products) >= _SEARCH_RETURN_LIMIT:
                    break

                item_id = item.get("id")
                title = item.get("title")
                price = item.get("price")
                permalink = item.get("permalink")
                thumbnail = item.get("thumbnail")

                if not all([item_id, title, permalink]):
                    logger.debug("Skipping item with missing fields: %s", item_id)
                    continue

                affiliate_link = await self._build_affiliate_link(
                    item_id, permalink, access_token, client
                )

                products.append(
                    ScrapedProduct(
                        title=title,
                        price=price,
                        link=affiliate_link,
                        image_url=thumbnail,
                        source="mercadolibre",
                    )
                )

        except Exception as e:
            logger.error("Error searching Mercado Livre products: %s", e)

        logger.info("MercadoLibre scraper returned %d products", len(products))
        return products
