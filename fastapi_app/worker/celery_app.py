import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "bitpulse",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    task_ignore_result=True
)


celery_app.autodiscover_tasks(['fastapi_app.worker'])


celery_app.conf.beat_schedule = {
    "update-prices-every-minute": {
        "task": "update_prices_task",
        "schedule": 60.0,
    },
}
