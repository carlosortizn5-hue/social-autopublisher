import tweepy
import logging
from app.publishers.base import Publisher
from app.models import Product
from app.config import settings

logger = logging.getLogger(__name__)


class TwitterPublisher(Publisher):
    def __init__(self):
        self.client = None
        if settings.x_bearer_token:
            self.client = tweepy.Client(bearer_token=settings.x_bearer_token)

    async def publish(self, product: Product, caption: str) -> tuple[bool, str]:
        if not self.client:
            return False, "Twitter credentials not configured"

        try:
            response = self.client.create_tweet(text=caption)
            tweet_id = response.data["id"]
            return True, f"Tweet {tweet_id} published"
        except Exception as e:
            logger.error(f"Error publishing to Twitter: {e}")
            return False, str(e)
