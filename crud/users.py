from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserModel
from schemas.users import CreateUser
from passlib.context import CryptContext

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
        return None

    result = await db.execute(stmt)
    return result.scalars().first()


async def create_user(db: AsyncSession, user: CreateUser):
    if await get_user(db, username=user.username):
        return None
    hashed_password = pwd_context.hash(user.password)
    new_user = UserModel(**user.model_dump(exclude=['password']), hashed_password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def verify_users(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username=username)
    if user is None:
        return False

    return pwd_context.verify(password, user.hashed_password)

    