from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from elasticsearch import AsyncElasticsearch
from redis.asyncio import from_url
from httpx import AsyncClient, ASGITransport
from dotenv import load_dotenv
from database.models import Base
import pytest
import os
import asyncio
from main import app
from database.database import get_session
from database.redis import get_redis


load_dotenv()

TEST_DB_URL = os.getenv('TEST_DATABASE_URL')
test_engine = create_async_engine(TEST_DB_URL)
TestSessionMaker = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope='session')
async def prepare_db():
    app.state.redis = from_url('redis://redis:6379/1', decode_responses=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await app.state.redis.aclose()


@pytest.fixture
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test'
    ) as client:
        yield client


@pytest.fixture
async def user_tokens(ac):
    payload = {'username': 'auth_user', 'email': 'unique@ya.ru', 'password': 'password123'}
    try:
        res1 = await ac.post('/auth/registration', json=payload)
        assert res1.status_code == 201
    except Exception:
        pass
    
    del payload['email']
    res2 = await ac.post("/auth/login", data=payload)
    assert res2.status_code == 200

    data = res2.json()
    access_token = data['access_token']
    refresh_token = data['refresh_token']
    return (access_token, refresh_token)


@pytest.fixture
async def auth_ac(ac, user_tokens):
    ac.headers.update({"Authorization": f"Bearer {user_tokens[0]}"})
    return ac


@pytest.fixture
async def db_session():
    async with TestSessionMaker() as session:
        yield session


@pytest.fixture
async def redis_client():
    yield app.state.redis
    await app.state.redis.flushdb() # очиста redis после каждого теста


@pytest.fixture(autouse=True)
def override_db(db_session, redis_client):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: redis_client
    yield
    app.dependency_overrides.clear()
    