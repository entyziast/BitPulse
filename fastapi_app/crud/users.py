from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserModel
from schemas.users import CreateUser
from passlib.context import CryptContext
from redis.asyncio import Redis
from crud.tickers import get_ticker_with_price, get_tickers_with_price
import exceptions.user_exceptions as user_exceptions


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_users(db: AsyncSession):
    stmt = select(UserModel)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_user(
    db: AsyncSession, 
    user_id: int | None = None,
    username: str | None = None,
):
    if user_id is not None:
        stmt = select(UserModel).where(UserModel.id==user_id)
    elif username is not None:
        stmt = select(UserModel).where(UserModel.username==username)
    else:
        raise user_exceptions.UserNotFoundException()

    
    result = await db.execute(stmt)
    user = result.scalars().one_or_none()
    if user is None:
        raise user_exceptions.UserNotFoundException()
    await db.refresh(user, ["tickers"])
    return user


async def get_user_with_prices(
    db: AsyncSession,
    redis: Redis,
    user: UserModel
):
    
    if not user:
        raise user_exceptions.UserNotFoundException()
    await db.refresh(user, ["tickers"])

    tickers_with_prices = await get_tickers_with_price(redis, user.tickers)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at, 
        "tickers": tickers_with_prices 
    }



async def create_user(db: AsyncSession, user: CreateUser):
    if await get_user(db, username=user.username):
        raise user_exceptions.UserAlreadyExistsException()

    hashed_password = pwd_context.hash(user.password)
    new_user = UserModel(**user.model_dump(exclude=['password']), hashed_password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def save_chat_id(db: AsyncSession, user_id: int, chat_id: int):
    stmt = update(UserModel).where(UserModel.id == user_id).values(tg_chat_id=chat_id)
    await db.execute(stmt)
    await db.commit()


async def delete_chat_id(db: AsyncSession, user_id: int):
    stmt = update(UserModel).where(UserModel.id == user_id).values(tg_chat_id=None)
    await db.execute(stmt)
    await db.commit()


async def verify_users(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username=username)
    if user is None:
        raise user_exceptions.UserNotFoundException()

    return pwd_context.verify(password, user.hashed_password)


REFRESH_TOKEN_EXPIRE_DAYS = 7
async def update_refresh_token(redis: Redis, username: str, refresh_token: str):
    key = f'refresh:{username}'
    await redis.set(key,refresh_token, ex=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

async def verify_refresh_token(redis: Redis, username: str, refresh_token: str):
    token_from_redis = await redis.get(f'refresh:{username}')
    return token_from_redis == refresh_token

async def delete_refresh_token(redis: Redis, username: str):
    key = f'refresh:{username}'
    await redis.delete(key)