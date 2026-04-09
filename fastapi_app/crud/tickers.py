from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from database.redis import get_redis
from database.models import TickerModel, UserModel
import json


RELEVANT_TICKER_PRICE_EXPIRE_TIME_SECONDS = 120


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


async def get_all_symbols_for_celery(
    db: AsyncSession
) -> list[str]:
    stmt = select(TickerModel.symbol)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_my_tickers(
    db: AsyncSession,
    user: UserModel
):
    await db.refresh(user, ["tickers"])
    return user.tickers


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


async def get_ticker_with_price(redis: Redis, ticker: TickerModel):
    price = await redis.get(f'price:{ticker.symbol.upper()}')

    return {
        "id": ticker.id,
        "symbol": ticker.symbol,
        "name": ticker.name,
        "price": float(price) if price else None
    }


async def get_tickers_with_price(redis: Redis, tickers: list[TickerModel]):
    if not tickers:
        return []

    keys = [f'price:{t.symbol}' for t in tickers]
    prices = await redis.mget(*keys)

    result = []
    for ticker, price in zip(tickers, prices):
        result.append({
            "id": ticker.id,
            "symbol": ticker.symbol,
            "name": ticker.name,
            "price": float(price) if price else None
        })
    return result



async def save_prices_in_redis(redis: Redis, data: list[str]):
    for ticker_data in data:
        await redis.publish(f'price:{ticker_data['symbol']}', ticker_data['price'])
        await redis.set(f'price:{ticker_data['symbol']}', ticker_data['price'], ex=RELEVANT_TICKER_PRICE_EXPIRE_TIME_SECONDS)
