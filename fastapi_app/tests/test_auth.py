from database.models import UserModel
from sqlalchemy import select
from api.auth import create_access_token
import pytest


@pytest.mark.anyio
async def test(ac):
    response = await ac.get('/tickers/all_tickers')
    assert response.status_code != 404


@pytest.mark.anyio
@pytest.mark.parametrize('username, email, password, expected_status', [
    ('long-username' * 3, 'test@yandex.ru', '12345678', 422),
    ('user', 'invalid-email', '12345678', 422),
    ('user', 'test@yandex.com', '', 422),
])
async def test_registration_validation(ac, username, email, password, expected_status):
    response = await ac.post('/auth/registration', json={
        'username': username, 'email': email, 'password': password
    })
    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_registration_logic_flow(ac):
    payload = {
        'username': 'norm_user', 
        'email': 'unique@ya.ru', 
        'password': 'password123'
    }
    
    res1 = await ac.post('/auth/registration', json=payload)
    assert res1.status_code == 201
    
    res2 = await ac.post('/auth/registration', json=payload)
    assert res2.status_code == 409


@pytest.mark.anyio
async def test_registration_full_check(ac, db_session):
    payload = {
        'username': 'database_warrior',
        'email': 'db_test@yandex.com',
        'password': 'super_secret_password'
    }

    response = await ac.post('/auth/registration', json=payload)
    assert response.status_code == 201

    query = select(UserModel).where(UserModel.email == payload['email'])
    result = await db_session.execute(query)
    user_in_db = result.scalar_one_or_none()

    assert user_in_db is not None
    assert user_in_db.username == payload['username']
    
    assert user_in_db.hashed_password != payload['password']


@pytest.mark.anyio
async def test_login_success(ac, redis_client):

    data = {
        "username": 'test_login',
        "email": "login@test.com",
        "password": "123321"
    }

    response = await ac.post('/auth/registration', json=data)
    assert response.status_code == 201

    del data['email']
    response = await ac.post("/auth/login", data=data) 

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    refresh_token_redis = await redis_client.get(f'refresh:test_login')
    assert data['refresh_token'] == refresh_token_redis.decode()


@pytest.mark.anyio
@pytest.mark.parametrize("username, password, expected_status", [
    ("test_login", "wrong_password", 401),
    ("non_existent@test.com", "secret_password", 404),
])
async def test_login_failures(ac, username, password, expected_status):
    response = await ac.post(
        "/auth/login", 
        data={"username": username, "password": password}
    )
    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_refresh_token_success(ac, user_tokens, redis_client):
    access_token_old, refresh_token_old = user_tokens
    
    response = await ac.post(
        "/auth/refresh", 
        params={"refresh_token": refresh_token_old}
    )
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    new_access = data["access_token"]
    new_refresh = data["refresh_token"]

    assert new_access != access_token_old
    assert new_refresh != refresh_token_old

    username = "auth_user"
    stored_token = await redis_client.get(f"refresh:{username}")
    
    assert stored_token is not None
    assert stored_token.decode() == new_refresh
    assert stored_token.decode() != refresh_token_old


@pytest.mark.anyio
async def test_refresh_token_invalid_or_expired(ac):
    bad_token = "invalid_token_string"
    response = await ac.post("/auth/refresh", params={"refresh_token": bad_token})
    
    assert response.status_code == 401


@pytest.mark.anyio
async def test_logout(auth_ac, redis_client):
    response = await auth_ac.get('/auth/logout')
    
    assert response.status_code == 200

    token_in_redis = await redis_client.get(f'refresh:auth_user')
    assert token_in_redis is None