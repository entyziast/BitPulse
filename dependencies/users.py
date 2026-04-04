from typing import Annotated
from fastapi import Path, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session
from database.models import UserModel
from crud.users import get_user
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


import os
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")




async def get_user_or_404(
    db: Annotated[AsyncSession, Depends(get_session)],
    username: Annotated[str, Path(title='user nickname')],
):
    user = await get_user(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail='This user is not found')
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception
    except jwt.exceptions.PyJWTError:
        raise HTTPException(status_code=400, detail='Unexpected error')
    user = await get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user