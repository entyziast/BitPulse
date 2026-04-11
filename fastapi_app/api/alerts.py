from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from schemas.alerts import AlertCreate, AlertShow, AlertStatus
from schemas.relations import AlertWithTicker
from dependencies.users import get_current_user
from database.database import get_session
from database.models import UserModel, AlertModel
import crud.alerts as crud_alerts
from dependencies.alerts import get_alert_dep


router = APIRouter(
    prefix='/alerts',
    tags=['alerts', ],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserMeDep = Annotated[UserModel, Depends(get_current_user)]
AlertDep = Annotated[AlertModel, Depends(get_alert_dep)]


@router.get(
    '/my_alerts',
    summary='Get my alerts',
    description='Retrieve all alerts created by the current user',
    response_model=list[AlertWithTicker]
)
async def get_my_alerts(
    db: SessionDep,
    user: UserMeDep,
):
    alerts = await crud_alerts.get_my_alerts(db, user)
    return alerts



@router.get(
    '/{alert_id}',
    summary='Get alert',
    description='Retrieve a specific alert by its ID',
    response_model=AlertWithTicker
)
async def get_my_alert(
    db: SessionDep,
    alert: AlertDep
) -> AlertWithTicker:

    return alert


@router.post(
    '/',
    summary='Create alert',
    description='''
    Create alert for ticker. 
    Alert will be triggered when the price of the ticker meets the specified condition. 
    Available operators: >, >=, <, <=
    ''',
    response_model=AlertWithTicker, 
    status_code=201
)
async def create_alert(
    db: SessionDep,
    user: UserMeDep,
    alert: AlertCreate,
) -> AlertWithTicker:
    new_alert = await crud_alerts.create_alert(db, user, alert)
    if new_alert is None:
        raise HTTPException(status_code=404, detail='Symbol does not exists')
    return new_alert


@router.delete(
    '/{alert_id}',
    summary='Delete alert',
    description='Delete a specific alert by its ID',
    status_code=204
)
async def delete_alert(
    db: SessionDep,
    alert: AlertDep,
) -> None:

    await crud_alerts.delete_alert(db, alert)


@router.patch(
    '/set_status/{alert_id}',
    summary='Activate/Deactivate alert',
    description='Activate or deactivate a specific alert by its ID.',
    response_model=AlertWithTicker
)
async def set_alert_status(
    db: SessionDep,
    alert: AlertDep,
    status: Annotated[AlertStatus, Query(..., description='Status of the alert: active or inactive')]
) -> AlertWithTicker:
    result = await crud_alerts.set_alert_status(db, alert, status.value)
    if result is None:
        raise HTTPException(status_code=400, detail='Invalid status value')
    return result