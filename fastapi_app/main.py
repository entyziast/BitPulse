from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from api import tickers, users, auth, alerts, telegram_webhook
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from worker.tasks import get_top50_tickers
from exceptions.main_exception import BitPulseException


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_top50_tickers.delay()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickers.router)
app.include_router(alerts.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(telegram_webhook.router)


@app.exception_handler(BitPulseException)
async def bitpulse_universal_handler(request, exc: BitPulseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)