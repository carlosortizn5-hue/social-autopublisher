import asyncio
import logging
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.config import settings
from app.models import Product, PostLog, PublishState
import os

os.environ.setdefault('DATABASE_URL', 'sqlite:///./social_autopublisher.db')
from app.scrapers.mercadolibre import MercadoLibreScraper
from app.publishers.twitter import TwitterPublisher
from app.publishers.meta import FacebookPublisher
from app.processors.normalizer import normalize_products
from app.processors.caption import generate_caption
from app.utils.locks import acquire_lock, release_lock

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


async def run_pipeline():
    db: Session = SessionLocal()
    
    try:
        logger.info("Starting social media publishing pipeline")
        
        # Step 1: Scrape from Mercado Libre
        logger.info("Scraping Mercado Libre...")
        ml_scraper = MercadoLibreScraper()
        ml_products = await ml_scraper.scrape()
        
        # Step 2: Normalize and store in DB
        logger.info(f"Processing {len(ml_products)} products")
        normalized = normalize_products(ml_products, db)
        db.add_all(normalized)
        db.commit()
        
        # Step 3: Publish pending products
        pending_products = db.query(Product).filter_by(state=PublishState.PENDING).limit(settings.posts_per_day).all()
        
        publishers = {
            "twitter": TwitterPublisher(),
            "facebook": FacebookPublisher(),
        }
        
        for product in pending_products:
            for platform, publisher in publishers.items():
                lock_key = f"publish:{product.id}:{platform}"
                
                if not acquire_lock(lock_key):
                    logger.info(f"Skipping {product.id} on {platform} (already publishing)")
                    continue
                
                try:
                    caption = generate_caption(product, platform)
                    success, message = await publisher.publish(product, caption)
                    
                    log_entry = PostLog(
                        product_id=product.id,
                        platform=platform,
                        status="success" if success else "failed",
                        message=message,
                    )
                    db.add(log_entry)
                    
                    if success:
                        product.state = PublishState.PUBLISHED
                        logger.info(f"Published {product.id} to {platform}")
                    else:
                        logger.error(f"Failed to publish {product.id} to {platform}: {message}")
                    
                    db.commit()
                except Exception as e:
                    logger.error(f"Error publishing {product.id} to {platform}: {e}")
                    log_entry = PostLog(
                        product_id=product.id,
                        platform=platform,
                        status="failed",
                        message=str(e),
                    )
                    db.add(log_entry)
                    db.commit()
                finally:
                    release_lock(lock_key)
        
        logger.info("Pipeline completed successfully")
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_pipeline())
