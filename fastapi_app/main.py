from fastapi import FastAPI
import uvicorn
from api import tickers, users, auth
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickers.router)
app.include_router(users.router)
app.include_router(auth.router)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)