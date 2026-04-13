from fastapi import APIRouter, Depends, Path, HTTPException
from database.database import get_session
from database.redis import get_redis
from database.models import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import crud.users as crud_users
from schemas.users import ShowUser
from schemas.relations import UserWithTickerPrices
from dependencies.users import get_current_user_with_ticker_prices
from redis import Redis


router = APIRouter(
    prefix='/users',
    tags=['users', ],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]


@router.get(
    '/', 
    response_model=list[ShowUser],
    summary='Get all users',
    description='Retrieve a list of all users registered in the system'
)
async def get_all_users(db: SessionDep) -> list[ShowUser]:
    return await crud_users.get_users(db)


@router.get(
    '/me', 
    response_model=UserWithTickerPrices,
    summary='Get current user',
    description='Retrieve information about the currently authenticated user'
)
async def get_user_me(
    db: SessionDep,
    redis: RedisDep,
    current_user: Annotated[UserModel, Depends(get_current_user_with_ticker_prices)]
):
    return current_user


@router.get(
    '/{username}', 
    response_model=ShowUser,
    summary='Get user by username',
    description='Retrieve information about a specific user by their username'
)
async def get_user(
    db: SessionDep,
    username: Annotated[str, Path(max_length=16)]
) -> ShowUser:
    user = await crud_users.get_user(db, username=username)

    return user




