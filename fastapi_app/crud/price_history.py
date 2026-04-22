from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TickerPriceHistoryModel
from exceptions.ticker_exceptions import TickerIDNotFoundException
import datetime


async def bulk_insert(db: AsyncSession, data: list[tuple[int, float]]):

    stmt = insert(TickerPriceHistoryModel)
    params = [
        {'ticker_id': ticker_id, 'price': price}
        for ticker_id, price in data
    ]

    await db.execute(
        stmt,
        params
    )

    await db.commit()


async def delete_old_prices(db: AsyncSession, older_than_hours: int = 24):
    cut_time = datetime.datetime.utcnow() - datetime.timedelta(hours=older_than_hours)

    stmt = delete(TickerPriceHistoryModel).where(TickerPriceHistoryModel.timestamp < cut_time)
    await db.execute(stmt)
    await db.commit()


async def get_ticker_price_history(db: AsyncSession, ticker_id: int):
    stmt = (
        select(TickerPriceHistoryModel)
        .where(TickerPriceHistoryModel.ticker_id == ticker_id)
        .order_by(TickerPriceHistoryModel.timestamp.asc())
    )

    result = await db.execute(stmt)
    ticker_price_history = result.scalars().all()

    if len(ticker_price_history) == 0:
        raise TickerIDNotFoundException(ticker_id)

    return ticker_price_history