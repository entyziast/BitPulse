from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os


load_dotenv()


def get_async_engine():
    return create_async_engine(
        url=os.getenv('DATABASE_URL'),
        future=True,
    )


def get_async_session_maker():
    async_engine = get_async_engine()
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session():
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session   

