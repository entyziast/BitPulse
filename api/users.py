from fastapi import APIRouter, Depends, Path, HTTPException
from database.database import get_session
from database.models import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import crud.users as crud_users
from schemas.users import ShowUser
from dependencies.users import get_current_user


router = APIRouter(
    prefix='/users',
    tags=['users', ],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.get('/', response_model=list[ShowUser])
async def get_all_users(db: SessionDep) -> list[ShowUser]:
    return await crud_users.get_users(db)

@router.get('/me', response_model=ShowUser)
async def get_user_me(
    db: SessionDep,
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    return current_user
    
@router.get('/{username}', response_model=ShowUser)
async def get_user(
    db: SessionDep,
    username: Annotated[str, Path(max_length=16)]
) -> ShowUser:
    user = await crud_users.get_user(db, username=username)

    if user is None:
        raise HTTPException(status_code=404, detail="Not found this user")
    return user




