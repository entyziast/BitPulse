from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends, Path, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import get_current_user, get_current_user_ws
from database.database import get_session
from database.models import UserModel
from database.redis import get_redis
from schemas.tickers import Ticker, TickerPrice
from schemas.relations import UserWithTickers
import exceptions.ticker_exceptions as ticker_exceptions
import crud.tickers as crud_tickers
from redis import Redis
from database.redis import get_redis
from typing import Annotated
from elasticsearch import AsyncElasticsearch
from database.elasticsearch import get_es_client

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
ElasticSearchDep = Annotated[AsyncElasticsearch, Depends(get_es_client)]


@router.get('/es_find/{ticker_id}')
async def get_ticker_from_elasticsearch(
    es: ElasticSearchDep,
    ticker_id: int
):
    try:
        ticker = await es.get(index="tickers", id=ticker_id)
    except Exception as e:
        raise ticker_exceptions.ESNotFoundError(ticker_id)
    return ticker


@router.post(
    '/subscribe/{symbol}', 
    response_model=UserWithTickers, 
    status_code=201,
    summary='Subscribe to ticker',
    description='''Subscribe current user to ticker by symbol. 
        If ticker does not exist in database, it will be created if it exists on BinanceAPI,
        otherwise exception 404 will be raised.'''
)
async def subscribe_to_ticker(
    db: SessionDep,
    user: UserMeDep,
    symbol: Annotated[str, Path(title='Name ticker')],
):
    try:
        ticker = await crud_tickers.get_ticker_by_symbol(db, symbol)
    except ticker_exceptions.TickerNotFoundException:
        # Ticker not found in db
        print(f"Ticker {symbol} not found in db. Trying to get info from Binance API...")
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
                raise ticker_exceptions.TickerNotExistInBinanceException(symbol)

    user = await crud_tickers.subscribe_ticker(db,symbol,user)
    return user


@router.delete(
    '/subscribe/{symbol}', 
    response_model=UserWithTickers,
    summary='Unsubscribe from ticker',
    description='''Unsubscribe current user from ticker by symbol.
        If user is not subscribed to ticker, nothing happens.'''
)
async def unsubscribe_to_ticker(
    db: SessionDep,
    user: UserMeDep,
    symbol: str,
):
    user = await crud_tickers.unsubscribe_ticker(db,symbol,user)
    return user


@router.get(
    '/my_tickers', 
    response_model=list[TickerPrice],
    summary='Get my tickers',
    description='Retrieve a list of tickers with prices that the current user is subscribed to'
)
async def get_my_tickers(
    db: SessionDep,
    redis: RedisDep,
    user: UserMeDep,
    offset: Annotated[int | None, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 10
):
    tickers = await crud_tickers.get_my_tickers(db, user, offset, limit)

    tickers_with_price = await crud_tickers.get_tickers_with_price(redis, tickers)
    return tickers_with_price


@router.get(
    '/all_tickers',
    response_model=list[Ticker],
    summary='Get all tickers',
    description='Retrieve a list of all tickers available in the database'
)
async def get_all_tickers(
    db: SessionDep,
    offset: Annotated[int | None, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 10
):
    tickers = await crud_tickers.get_all_tickers_info(db, offset, limit)
    return tickers


@router.get(
    '/polling_ticker_prices', 
    summary='Polling ticker prices',
    description='''Endpoint for polling ticker prices from Binance API.
        This endpoint is intended to be used by Celery beat 
        for periodic polling of ticker prices and saving them in Redis.'''
)
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


@router.get('/{id_or_symbol}', response_model=TickerPrice)
async def get_ticker_info(
    db: SessionDep,
    redis: RedisDep,
    id_or_symbol: str = Path(title='ID or symbol of ticker')
):
    if id_or_symbol.isdigit():
        ticker = await crud_tickers.get_ticker_by_id(db, int(id_or_symbol))
    else:
        ticker = await crud_tickers.get_ticker_by_symbol(db, id_or_symbol)

    ticker_with_price = await crud_tickers.get_ticker_with_price(redis, ticker)

    return ticker_with_price


@router.websocket('/ws', name='WebSocket for real-time ticker price updates')
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