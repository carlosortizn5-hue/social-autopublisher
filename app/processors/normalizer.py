from typing import List
from app.scrapers.base import ScrapedProduct
from app.models import Product
from sqlalchemy.orm import Session


def normalize_products(raw_products: List[ScrapedProduct], db: Session) -> List[Product]:
    """Convert scraped products to DB models with dedup by unique link constraint"""
    normalized = []

    for raw in raw_products:
        existing = db.query(Product).filter_by(link=raw.link).first()
        if existing:
            continue  # Skip if already in DB

        product = Product(
            title=raw.title[:500],
            price=raw.price,
            link=raw.link,
            image_url=raw.image_url[:2000] if raw.image_url else None,
            source=raw.source,
            affiliate_tag=getattr(raw, "affiliate_tag", None),
        )
        normalized.append(product)

    return normalized
