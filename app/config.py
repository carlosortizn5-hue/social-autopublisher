from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./social_autopublisher.db'
    redis_url: str = 'redis://localhost:6379/0'
    is_production: bool = False
    posts_per_day: int = 3
    pipeline_internal_token: str = 'dev-token'
    log_level: str = 'INFO'
    ml_client_id: Optional[str] = None
    ml_client_secret: Optional[str] = None
    ml_refresh_token: Optional[str] = None
    ml_affiliate_tag: Optional[str] = None
    ml_site_id: Optional[str] = None
    ml_search_query: Optional[str] = None
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    x_access_token: Optional[str] = None
    x_access_token_secret: Optional[str] = None
    x_bearer_token: Optional[str] = None
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_long_lived_token: Optional[str] = None
    ig_business_account_id: Optional[str] = None
    fb_page_id: Optional[str] = None
    class Config:
        env_file = '.env'
        case_sensitive = False

settings = Settings()
