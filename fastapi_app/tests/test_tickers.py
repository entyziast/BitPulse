import pytest
import respx


@pytest.mark.anyio
@pytest.mark.parametrize('symbol, expected_status_sub, expected_status_get', [
    ('BTCUSDT', 201, 200),
    ('ABCDEFZZZ', 404, 404),
])
async def test_subscribe_get_unsubscribe_ticker(
    auth_ac, 
    symbol, 
    expected_status_sub, 
    expected_status_get
):
    response = await auth_ac.post(f'tickers/subscribe/{symbol}')
    assert response.status_code == expected_status_sub
    data = response.json()

    if response.status_code == 201:
        assert any(ticker['symbol'] == symbol for ticker in data['tickers'])
    

    response = await auth_ac.get(f'tickers/{symbol}')
    assert response.status_code == expected_status_get

    response = await auth_ac.get(f'tickers/my_tickers')
    assert response.status_code == 200
    my_tickers = response.json()
    assert isinstance(my_tickers, list)
    if expected_status_get < 300:
        assert any(ticker['symbol'] == symbol for ticker in my_tickers)
    else:
        assert not any(ticker['symbol'] == symbol for ticker in my_tickers)

    del_response = await auth_ac.delete(f'tickers/subscribe/{symbol}')
    assert del_response.status_code == expected_status_get
    if del_response.status_code != 404:
        del_data = del_response.json()
        assert all(t['symbol'] != symbol for t in del_data['tickers'])

    response = await auth_ac.get('tickers/my_tickers')
    my_tickers_after = response.json()
    assert all(t['symbol'] != symbol for t in my_tickers_after)

    
@pytest.mark.anyio
async def test_my_tickers_with_redis_price(auth_ac, redis_client):
    symbol = "BTCUSDT"
    await redis_client.set(f"price:{symbol}", "60000.50")
    
    await auth_ac.post(f'tickers/subscribe/{symbol}')
    response = await auth_ac.get('tickers/my_tickers')
    
    data = response.json()
    ticker = next(t for t in data if t['symbol'] == symbol)
    assert float(ticker['price']) == 60000.50

