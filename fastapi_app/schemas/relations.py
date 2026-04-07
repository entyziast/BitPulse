from schemas import tickers, users
from pydantic import BaseModel


class UserWithTickers(users.ShowUser):
    tickers: list[tickers.Ticker]

class UserWithTickerPrices(users.ShowUser):
    tickers: list[tickers.TickerPrice]

class TickerWithSubcribers(tickers.Ticker):
    subcribers: list[users.ShowUser]