from abc import ABC, abstractmethod
from app.models import Product


class Publisher(ABC):
    @abstractmethod
    async def publish(self, product: Product, caption: str) -> tuple[bool, str]:
        pass
