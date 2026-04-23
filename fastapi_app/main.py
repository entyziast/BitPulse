from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import Redis
from redis.asyncio import from_url
from database.redis import get_redis
import uvicorn
from api import tickers, users, auth, alerts, tg_integration
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from worker.tasks import get_top50_tickers
from exceptions.main_exception import BitPulseException
import os
import datetime


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_pool = from_url(os.getenv("REDIS_URL"), decode_responses=False)
    app.state.redis = redis_pool
    get_top50_tickers.delay()
    yield
    await redis_pool.close()

app = FastAPI(lifespan=lifespan)

TOKENS_PER_SECOND=int(os.getenv('TOKENS_PER_SECOND'))
BUCKET_CAPACITY=int(os.getenv('BUCKET_CAPACITY'))

@app.middleware("http")
async def rate_limit_middleware(request, call_next):

    redis = request.app.state.redis 
    client_ip = request.client.host

    data = await redis.hgetall(f'rate_limit:{client_ip}')

    if data:
        old_tokens = float(data.get(b'tokens'))
        old_timestamp = float(data.get(b'timestamp'))

        elapsed = (datetime.datetime.now() - datetime.datetime.fromtimestamp(old_timestamp)).total_seconds()
        cur_tokens = min(BUCKET_CAPACITY, old_tokens + elapsed*TOKENS_PER_SECOND)
    else:
        cur_tokens = BUCKET_CAPACITY

    if cur_tokens < 1:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    async with redis.pipeline() as pipe:
        pipe.hset(
            f'rate_limit:{client_ip}',
            mapping={
                'tokens': cur_tokens - 1,
                'timestamp': datetime.datetime.now().timestamp()
            }
        )
        pipe.expire(f'rate_limit:{client_ip}', BUCKET_CAPACITY//TOKENS_PER_SECOND)
        await pipe.execute()

    response = await call_next(request)
    return response 


app.include_router(tickers.router)
app.include_router(tg_integration.router)
app.include_router(alerts.router)
app.include_router(users.router)
app.include_router(auth.router)


@app.exception_handler(BitPulseException)
async def bitpulse_universal_handler(request, exc: BitPulseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)