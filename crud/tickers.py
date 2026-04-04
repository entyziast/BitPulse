from redis import Redis
from database.redis import get_redis
import json

async def save_prices(redis: Redis, data: list[str]):

    for ticker_data in data:
        await redis.publish('prices', json.dumps(ticker_data))

