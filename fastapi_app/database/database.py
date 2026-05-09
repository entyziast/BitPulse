from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os


DATABASE_URL = os.getenv('DATABASE_URL')

async_engine = create_async_engine(
    url=DATABASE_URL,
    pool_size=30,
    max_overflow=10,
    pool_timeout=5,
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with async_session_factory() as session:
        yield session

