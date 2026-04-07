from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dotenv import load_dotenv
import os


load_dotenv()
async_engine = create_async_engine(
    url=os.getenv('DATABASE_URL'),
    future=True,
    echo=True,
)


async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session():
    async with async_session() as session:
        yield session   
