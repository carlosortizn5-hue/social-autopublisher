from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from app.db import Base
from datetime import datetime


class PublishState:
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=True)
    link = Column(String(2000), nullable=False, unique=True)
    image_url = Column(String(2000), nullable=True)
    source = Column(String(50), nullable=False)
    affiliate_tag = Column(String(200), nullable=True)
    state = Column(String(50), default=PublishState.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    first_published_at = Column(DateTime, nullable=True)


class PostLog(Base):
    __tablename__ = "post_log"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)


class PlatformToken(Base):
    __tablename__ = "platform_tokens"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), unique=True, nullable=False)
    token = Column(String(2000), nullable=False)
    refresh_token = Column(String(2000), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
