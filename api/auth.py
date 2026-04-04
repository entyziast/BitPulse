from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
import os
from dotenv import load_dotenv
from schemas.users import ShowUser, CreateUser, TokenResponse
import crud.users as crud_users


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(
    prefix='/auth',
    tags=['users', 'auth'],
)


@router.post('/registration', response_model=ShowUser, status_code=201)
async def registration(db: SessionDep, user: CreateUser) -> ShowUser:
    new_user = await crud_users.create_user(db, user)
    if new_user is None:
        raise HTTPException(status_code=409, detail='This user already exists')
    return new_user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post('/login', response_model=TokenResponse)
async def login(
    db: SessionDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    if not await crud_users.verify_users(db, form.username, form.password):
        raise HTTPException(status_code=400, detail='Wrong username or password!')

    token = create_access_token(data={"sub": form.username})
    return TokenResponse(access_token=token, token_type="bearer")
