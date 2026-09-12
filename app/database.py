import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase):
    pass

DB_URL = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
engine = create_async_engine(DB_URL, echo=False, pool_size=10, max_overflow=20)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
