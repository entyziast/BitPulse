from typing import Annotated
from redis import Redis
from fastapi import HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import get_current_user
from database.database import get_session
from database.redis import get_redis
from database.models import UserModel, AlertModel
from crud.alerts import get_alert
from exceptions.user_exceptions import ForbiddenUserException


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserMeDep = Annotated[UserModel, Depends(get_current_user)]
RedisDep = Annotated[Redis, Depends(get_redis)]



async def get_alert_dep(
    db: SessionDep,
    redis: RedisDep,
    user: UserMeDep,
    alert_id: Annotated[int, Path(title='Alert ID')],
) -> AlertModel:
    alert = await get_alert(db, alert_id)
    if alert.user_id != user.id:
        raise ForbiddenUserException()

    return alert