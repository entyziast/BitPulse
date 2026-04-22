from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TickerPriceHistoryModel
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