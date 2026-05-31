from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel


class ScrapedProduct(BaseModel):
    title: str
    price: float | None = None
    link: str
    image_url: str | None = None
    source: str


class Scraper(ABC):
    @abstractmethod
    async def scrape(self) -> List[ScrapedProduct]:
        pass
