from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session
from datetime import datetime, timedelta, timezone
from database.redis import get_redis
from redis.asyncio import Redis
from typing import Annotated
import jwt
import os
from dotenv import load_dotenv
from schemas.users import ShowUser, CreateUser, TokenResponse
import crud.users as crud_users
from dependencies.users import get_current_user
import exceptions.user_exceptions as user_exceptions


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]

router = APIRouter(
    prefix='/auth',
    tags=['users', 'auth'],
)


@router.post(
    '/registration', 
    response_model=ShowUser, 
    status_code=201,
    summary='User registration',
    description='Create a new user account with the provided username and password'
)
async def registration(db: SessionDep, user: CreateUser) -> ShowUser:
    new_user = await crud_users.create_user(db, user)

    return new_user


def create_access_token(
    data: dict, 
    expires_delta: timedelta | None = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"}) 
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post(
    '/login', 
    response_model=TokenResponse,
    summary='User login',
    description='Authenticate user and return access and refresh bearer tokens'
)
async def login(
    db: SessionDep,
    redis: RedisDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    if not await crud_users.verify_users(db, form.username, form.password):
        raise user_exceptions.UserWrongPasswordException()

    access_payload = {"sub": form.username}
    access_token = create_access_token(data=access_payload)
    refresh_token = create_refresh_token(data=access_payload)

    await crud_users.update_refresh_token(redis, form.username, refresh_token)
    response = TokenResponse(
        access_token=access_token, 
        refresh_token=refresh_token, 
        token_type="bearer"
    )
    return response

@router.post(
    '/refresh', 
    response_model=TokenResponse,
    summary='Refresh access token',
    description='Refresh access token using valid refresh token'
)
async def refresh_token(
    redis: RedisDep,
    refresh_token: str
) -> TokenResponse:
    
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if payload.get("type") != "refresh":
        raise user_exceptions.UserErrorToUpdateRefreshTokenException(username)
    

    
    if not (await crud_users.verify_refresh_token(redis, username, refresh_token)):
        raise user_exceptions.UserErrorToUpdateRefreshTokenException(username)

    new_access = create_access_token({"sub": username})
    new_refresh = create_refresh_token({"sub": username})
    
    await crud_users.update_refresh_token(redis, username, new_refresh)
    response = TokenResponse(
        access_token=new_access, 
        refresh_token=new_refresh, 
        token_type="bearer"
    )
    return response


@router.get(
    '/logout',
    summary='User logout',
    description='Logout user from server by deleting refresh token from database'
)
async def logout(
    redis: RedisDep,
    current_user: Annotated[ShowUser, Depends(get_current_user)],
):
    result = await crud_users.delete_refresh_token(redis, current_user.username)
    return {"detail": "Logged out from server"}