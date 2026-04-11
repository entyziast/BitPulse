from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserModel, AlertModel
from schemas.alerts import AlertCreate, AlertType, AlertStatus
from crud.tickers import get_ticker_by_symbol


async def get_my_alerts(
    db: AsyncSession,
    user: UserModel,
):
    stmt = (
        select(AlertModel)
        .where(AlertModel.user_id==user.id)
        .options(selectinload(AlertModel.ticker))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
    

async def get_alert(
    db: AsyncSession,
    alert_id: int
):
    stmt = select(AlertModel).where(AlertModel.id==alert_id)

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if alert:
        await db.refresh(alert, ['ticker'])
    return alert 

async def create_alert(
    db: AsyncSession,
    user: UserModel,
    alert: AlertCreate
):
    ticker = await get_ticker_by_symbol(db, alert.symbol)
    if ticker is None:
        return None

    alert_dict = alert.model_dump()

    if alert_dict['alert_type'] == AlertType.PRICE_THRESHOLD:
        target_value = alert_dict['value']
    
    alert_dict.pop('value')
    alert_dict.pop('symbol')

    new_alert = AlertModel(
        **alert_dict,
        user_id=user.id,
        ticker_id=ticker.id,
        target_value=target_value,
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert, ["ticker"])
    return new_alert


async def delete_alert(
    db: AsyncSession,
    alert: AlertModel,
):
    await db.delete(alert)
    await db.commit()


async def get_all_active_alerts(db: AsyncSession):
    stmt = select(AlertModel).where(AlertModel.is_active==True).options(selectinload(AlertModel.ticker))
    result = await db.execute(stmt)

    return result.scalars().all()


async def set_alert_status(
    db: AsyncSession,
    alert: AlertModel,
    status: AlertStatus
):
    if status == AlertStatus.ACTIVE:
        alert.is_active = True
        alert.triggered_at = None
    elif status == AlertStatus.INACTIVE:
        alert.is_active = False
        alert.triggered_at = None
    else:
        return None

    await db.commit()
    await db.refresh(alert, ["ticker"])
    return alert