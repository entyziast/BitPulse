from typing import Annotated
from fastapi import HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import get_current_user
from database.database import get_session
from database.models import UserModel, AlertModel
from crud.alerts import get_alert


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserMeDep = Annotated[UserModel, Depends(get_current_user)]


async def get_alert_dep(
    db: SessionDep,
    user: UserMeDep,
    alert_id: Annotated[int, Path(title='Alert ID')],
) -> AlertModel:
    alert = await get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail='This alert does not exist')
    elif alert.user_id != user.id:
        raise HTTPException(status_code=404, detail='Forbidden alert!')

    return alert