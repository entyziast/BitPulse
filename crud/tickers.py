from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from database.redis import get_redis
from database.models import TickerModel, UserModel
import json


RELEVANT_TICKER_PRICE_EXPIRE_TIME_SECONDS = 60


async def get_ticker_by_symbol(
    db: AsyncSession,
    symbol: str
):
    stmt = (
        select(TickerModel).where(TickerModel.symbol==symbol.upper())
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_tickers_info(
    db: AsyncSession,
    offset: int | None = 0,
    limit: int | None = 10,
):
    stmt = (
        select(TickerModel)
        .order_by(TiсkerModel.symbol)
        .offset(offset=offset)
        .limit(limit=limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_ticker(
    db: AsyncSession,
    ticker_symbol: str,
    ticker_name: str
):
    new_ticker = TickerModel(symbol=ticker_symbol, name=ticker_name)

    db.add(new_ticker)
    await db.commit()
    await db.refresh(new_ticker)
    return new_ticker



async def subscribe_ticker(
    db: AsyncSession,
    symbol: str,
    user: UserModel
):
    ticker = await get_ticker_by_symbol(db, symbol)
    if ticker is None:
        return None
    
    await db.refresh(user, ["tickers"])

    if ticker not in user.tickers:
        user.tickers.append(ticker)
        await db.commit()
        await db.refresh(user, ["tickers"])
    
    return user


async def unsubscribe_ticker(
    db: AsyncSession,
    symbol: str,
    user: UserModel
):
    ticker = await get_ticker_by_symbol(db, symbol)
    if ticker is None:
        return None

    await db.refresh(user, ["tickers"])

    if ticker in user.tickers:
        user.tickers.remove(ticker)
        await db.commit()
    
    return user


async def save_prices_in_redis(redis: Redis, data: list[str]):
    for ticker_data in data:
        await redis.publish(f'prices{ticker_data['symbol']}', ticker_data['price'])
        await redis.set(f'prices{ticker_data['symbol']}', ticker_data['price'], ex=RELEVANT_TICKER_PRICE_EXPIRE_TIME_SECONDS)
