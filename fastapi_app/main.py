from fastapi import FastAPI
import uvicorn
from api import tickers, users, auth, alerts
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from worker.tasks import get_top50_tickers

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






if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)