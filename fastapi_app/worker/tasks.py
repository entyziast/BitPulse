import asyncio
import datetime
import json
import httpx
import re
import os
from .celery_app import celery_app
from database.redis import get_redis
from database.database import get_async_session_maker
from schemas.alerts import AlertStatus
from crud.tickers import (
    save_prices_in_redis, 
    create_ticker, 
    get_ticker_by_symbol, 
    get_all_symbols_for_celery,
    get_all_tickers_for_es,
)
from crud.alerts import get_all_active_alerts
from exceptions.ticker_exceptions import TickerNotFoundException
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk






@celery_app.task(name='check_alerts_task')
def check_alerts_task():
    return asyncio.run(run_check_alerts())

async def run_check_alerts():
    
    session_factory = get_async_session_maker()
    async with session_factory() as db:
        active_alerts = await get_all_active_alerts(db)
    
        import operator
        OPERATORS = {
            '>': operator.gt,
            '>=': operator.ge,
            '<': operator.lt,
            '<=': operator.le,
        }
        
        redis = await get_redis()
        triggered_count = 0
        for alert in active_alerts:
            alert_price = await redis.get(f'price:{alert.ticker.symbol}')
            if alert_price is None:
                print(f"Price for {alert.ticker.symbol} not found in Redis.")
                continue
            alert_price = float(alert_price)
            
            
            if OPERATORS[alert.alert_operator.value](alert_price, alert.target_value) or alert.alert_type == AlertStatus.ALWAYS_TRIGGER:
                alert.alert_status = AlertStatus.TRIGGERED
                alert.triggered_at = datetime.datetime.utcnow()
                triggered_count += 1

        await db.commit()
        await redis.aclose()
    return f"Checked {len(active_alerts)} alerts, triggered {triggered_count}."



@celery_app.task(name="update_prices_task")
def update_prices_task():
    """Синхронная обертка для update_prices_task"""
    return asyncio.run(request_to_binanceAPI_get_prices())


async def request_to_binanceAPI_get_prices():
    
    session_factory = get_async_session_maker()
    async with session_factory() as db:
        symbols = await get_all_symbols_for_celery(db)

    if not symbols:
        return "No tickers found in database to update."

    url = "https://api.binance.com/api/v3/ticker/price"
    params = {
        'symbols' : json.dumps(symbols, separators=(",", ":"))
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get('msg', 'Unknown Binance Error')
                print(f"!!! Binance rejected symbols: {error_msg}")
                return f"Error: {error_msg}"
            
            redis = await get_redis()
            
            await save_prices_in_redis(redis, data)

            check_alerts_task.delay()

            await redis.aclose()
            
            return f"Updated {len(data)} tickers"
        except Exception as e:
            print(f"Error in background task update_prices_task: {e}")


@celery_app.task(name="sync_ticker_to_elasticsearch")
def sync_ticker_to_elasticsearch(ticker_id: int, symbol: str, name: str):
    return asyncio.run(fill_new_ticker_to_elasticsearch(ticker_id, symbol, name))


async def fill_new_ticker_to_elasticsearch(ticker_id: int, symbol: str, name: str):
    es = AsyncElasticsearch(hosts=[os.getenv('ELASTICSEARCH_URL')])

    try:
        doc = {
            'symbol': symbol,
            'name': name
        }
        await es.index(
            index='tickers',
            id=ticker_id,
            document=doc
        )
        return f"Successfully indexed ticker {symbol} to Elasticsearch."

    finally:
        await es.close()


@celery_app.task(name="sync_new_tickers_to_elasticsearch")
def sync_new_tickers_to_elasticsearch():
    return asyncio.run(fill_elasticsearch())

async def fill_elasticsearch():
    es = AsyncElasticsearch(hosts=[os.getenv('ELASTICSEARCH_URL')])

    try:
        if not await es.indices.exists(index="tickers"):
            from database.elasticsearch import ES_TICKERS_MAPPING
            await es.indices.create(index="tickers", mappings=ES_TICKERS_MAPPING)
            # index is empty, we must fill it with all tickers from db

        session_factory = get_async_session_maker()
        async with session_factory() as db:
            tickers_info = await get_all_tickers_for_es(db)

        actions = [
            {
                "_op_type": "index",
                "_index": "tickers",
                "_id": str(ticker_id),
                "_source":{
                    "symbol": symbol,
                    "name": name
                }
            }
            for ticker_id, symbol, name in tickers_info
        ]

        success, errors = await async_bulk(es, actions)
        return f"Successfully indexed {success} tickers to Elasticsearch. Errors: {len(errors)}"
    finally:
        await es.close()


@celery_app.task(name="get_top50_tickers")
def get_top50_tickers():
    return asyncio.run(request_get_top50_tickers())


async def request_get_top50_tickers():
    url = 'https://api.binance.com/api/v3/ticker/24hr'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = response.json()

            tickers_usdt = [
                ticker for ticker in data 
                if ticker['symbol'].endswith('USDT') and re.match(r'^[A-Z0-9]+$', ticker['symbol'])
            ]

            top50_tickers = sorted(
                tickers_usdt,
                key=lambda x: float(x['quoteVolume']),
                reverse=True
            )[:50]

            session_factory = get_async_session_maker()
            new_tickers_count = 0

            async with session_factory() as db:
                for ticker in top50_tickers:
                    symbol = ticker['symbol']
                    try:
                        await get_ticker_by_symbol(db, symbol)
                    except TickerNotFoundException:
                        new_tickers_count += 1
                        new_ticker = await create_ticker(db, symbol, symbol[:-4])

                sync_new_tickers_to_elasticsearch.delay()
                return f"Successfully found {len(top50_tickers)} tickers. Added {new_tickers_count} new tickers into db."

        except Exception as e:
            return f"Error in get_top50_tickers: {e}"