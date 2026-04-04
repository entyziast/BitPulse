from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends
from dependencies.users import get_current_user
from database.database import get_session
from database.redis import get_redis
import crud.tickers as crud_tickers
from redis import Redis
from database.redis import get_redis
from typing import Annotated

import websockets
import httpx
import json

router = APIRouter(
    prefix='/tickers',
    tags=['tickers', ],
)

tickers = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT",
    "MATICUSDT", "LTCUSDT", "LINKUSDT", "BCHUSDT", "ATOMUSDT",
    "XLMUSDT", "UNIUSDT", "ETCUSDT", "ICPUSDT", "FILUSDT",
    "APTUSDT", "ARBUSDT", "OPUSDT", "NEARUSDT", "ALGOUSDT",
    "VETUSDT", "HBARUSDT", "EGLDUSDT", "AAVEUSDT", "SANDUSDT",
    "MANAUSDT", "AXSUSDT", "THETAUSDT", "FTMUSDT", "XTZUSDT",
    "FLOWUSDT", "CHZUSDT", "GRTUSDT", "ENJUSDT", "KAVAUSDT",
    "ZECUSDT", "DASHUSDT", "SNXUSDT", "CRVUSDT", "1INCHUSDT",
    "RUNEUSDT", "LDOUSDT", "PEPEUSDT", "SHIBUSDT", "BLURUSDT"
]


@router.get('/')
def test():
    return {'q': 123}


@router.get('/connect_to_binanceapi')
async def connect_to_binanceapi(redis: Annotated[Redis, Depends(get_redis)]):
    url = "https://api.binance.com/api/v3/ticker/price"
    

    params = {
        'symbols' : json.dumps(tickers, separators=(",", ":"))
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url,params=params)
        data = response.json()
        await crud_tickers.save_prices(redis, data)
    
    return {'response' : data}

@router.websocket('/ws')
async def ws_prices(websocket: WebSocket, redis: Annotated[Redis, Depends(get_redis)]):
    await websocket.accept()

    pubsub = redis.pubsub()
    await pubsub.subscribe('prices')
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
                print(data)
    except Exception:
        print(f"WS Error: {e}")
    finally:
        await pubsub.unsubscribe('prices')
        await websocket.close()