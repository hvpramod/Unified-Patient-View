from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
import redis.asyncio as aioredis

engine = create_async_engine(settings.database_url, pool_size=20, max_overflow=10)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis():
    # protocol=2 ensures RESP2 — compatible with Redis < 6 (Windows Redis)
    client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True, protocol=2)
    try:
        yield client
    finally:
        await client.aclose()
