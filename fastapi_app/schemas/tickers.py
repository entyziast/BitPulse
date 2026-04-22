from pydantic import BaseModel
import datetime

class TickerBase(BaseModel):
    symbol: str
    name: str

    model_config = {"from_attributes": True}


class TickerCreate(TickerBase):
    pass

class Ticker(TickerBase):
    id: int

class TickerPrice(Ticker):
    price: float | None = None

class TickerPriceHistory(BaseModel):
    price: float
    timestamp: datetime.datetime

    model_config = {"from_attributes": True}