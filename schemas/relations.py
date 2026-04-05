from schemas import tickers, users
from pydantic import BaseModel


class UserWithTickers(users.ShowUser):
    tickers: list[tickers.Ticker]

class TickerWithSubcribers(tickers.Ticker):
    subcribers: list[users.ShowUser]