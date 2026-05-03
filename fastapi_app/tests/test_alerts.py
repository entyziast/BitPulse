import pytest


@pytest.mark.anyio
async def test_alerts_not_auth(ac):
    response = await ac.post('/alerts/')
    assert response.status_code == 401

    response = await ac.get('/alerts/my_alerts')
    assert response.status_code == 401

    response = await ac.get('/alerts/enable_tg_notifications')
    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize('symbol, value, alert_type, alert_operator, expected_status', [
    ('BTCUSDT', 10000, 'always_trigger', '>', 201)
])
async def test_alerts(auth_ac, symbol, value, alert_type, alert_operator, expected_status):

    payload = {
        'symbol': symbol,
        'value': value,
        'alert_type': alert_type,
        'alert_operator': alert_operator
    }

    create_response = await auth_ac.post(
        '/alerts/', 
        json=payload
    )

    assert create_response.status_code == 404

    await auth_ac.post(f'tickers/subscribe/{symbol}')

    create_response = await auth_ac.post(
        '/alerts/', 
        json=payload
    )
    assert create_response.status_code == expected_status

    alert_id = create_response.json()['id']

    get_res = await auth_ac.get(f'/alerts/{alert_id}')
    assert get_res.status_code == 200
    assert get_res.json()['ticker']['symbol'] == symbol

    list_res = await auth_ac.get('/alerts/my_alerts')
    assert list_res.status_code == 200
    assert any(a['id'] == alert_id for a in list_res.json())

    patch_res = await auth_ac.patch(f'/alerts/set_status/{alert_id}?status=inactive')
    assert patch_res.status_code == 200
    assert patch_res.json()['alert_status'] == 'inactive'

    del_res = await auth_ac.delete(f'/alerts/{alert_id}')
    assert del_res.status_code == 204

    final_get_res = await auth_ac.get(f'/alerts/{alert_id}')
    assert final_get_res.status_code == 404


