from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import get_current_user
from database.database import get_session
from database.models import UserModel
from database.redis import get_redis
from schemas.tickers import Ticker
from schemas.relations import UserWithTickers
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

SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserMeDep = Annotated[UserModel, Depends(get_current_user)]
RedisDep = Annotated[Redis, Depends(get_redis)]


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


@router.post('/subscribe/{symbol}', response_model=UserWithTickers, status_code=201)
async def subscribe_to_ticker(
    db: SessionDep,
    user: UserMeDep,
    symbol: Annotated[str, Path(title='Name ticker')]
):

    ticker = await crud_tickers.get_ticker_by_symbol(db, symbol)

    if ticker is None:
        # Ticker not found in db
        url = 'https://api.binance.com/api/v3/exchangeInfo'
        params = {
            'symbol' : symbol.upper()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url=url,params=params)
            if response.status_code == 200:
                data = response.json()
                ticker_data = data['symbols'][0]
                symbol = ticker_data['symbol']
                name = ticker_data['baseAsset']
                await crud_tickers.create_ticker(db, ticker_symbol=symbol, ticker_name=name)
            else:
                raise HTTPException(status_code=response.status_code, detail='Error to find this ticker in Binance API')

    user = await crud_tickers.subscribe_ticker(db,symbol,user)
    return user


@router.get('/polling_ticker_prices', description='HTTP request to Binance API, polling price tickers')
async def polling_ticker_prices(redis: Annotated[Redis, Depends(get_redis)]):
    url = "https://api.binance.com/api/v3/ticker/price"
    

    params = {
        'symbols' : json.dumps(tickers, separators=(",", ":"))
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url,params=params)
        data = response.json()
        await crud_tickers.save_prices_in_redis(redis, data)
    
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