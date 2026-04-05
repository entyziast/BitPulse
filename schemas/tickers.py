from pydantic import BaseModel


class TickerBase(BaseModel):
    symbol: str
    name: str

    model_config = {"from_attributes": True}


class TickerCreate(TickerBase):
    pass

class Ticker(TickerBase):
    id: int