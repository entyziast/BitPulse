from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import get_current_user, get_current_user_ws
from database.database import get_session
from database.models import UserModel
from database.redis import get_redis
from schemas.tickers import Ticker, TickerPrice
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
UserMeWebSocketDep = Annotated[UserModel, Depends(get_current_user_ws)]


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


@router.delete('/subscribe/{symbol}', response_model=UserWithTickers)
async def unsubscribe_to_ticker(
    db: SessionDep,
    user: UserMeDep,
    symbol: str
):
    user = await crud_tickers.unsubscribe_ticker(db,symbol,user)
    if user is None:
        raise HTTPException(status_code=404, detail='Not found this ticker in db')
    return user


@router.get('/my_tickers', response_model=list[TickerPrice])
async def get_my_tickers(
    db: SessionDep,
    redis: RedisDep,
    user: UserMeDep,
):
    tickers = await crud_tickers.get_my_tickers(db, user)

    tickers_with_price = await crud_tickers.get_tickers_with_price(redis, tickers)
    return tickers_with_price

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


@router.get('/{symbol}', response_model=TickerPrice)
async def get_ticker_info(
    db: SessionDep,
    redis: RedisDep,
    symbol: str
):
    ticker = await crud_tickers.get_ticker_by_symbol(db, symbol)

    if ticker is None:
        raise HTTPException(status_code=404, detail='Not found this ticker in db, to add him you must subcribe!')

    ticker_with_price = await crud_tickers.get_ticker_with_price(redis, ticker)

    return ticker_with_price



@router.websocket('/ws')
async def ws_prices(
    websocket: WebSocket,
    db: SessionDep,
    user: UserMeWebSocketDep,
    redis: RedisDep
):
    if user is None:
        await websocket.accept()
        await websocket.close(code=4008)
        return

    await websocket.accept()

    pubsub = redis.pubsub()
    relevant_tickers = await crud_tickers.get_my_tickers(db, user)
    relevant_channels = [f'price:{ticker.symbol}' for ticker in relevant_tickers]
    await pubsub.subscribe(*relevant_channels)

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':

                symbol = message['channel'][6:]
                price = float(message['data'])

                data = {
                    'symbol': symbol,
                    'price': price
                }
                await websocket.send_json(data)
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await pubsub.unsubscribe(*relevant_channels)
        await websocket.close()