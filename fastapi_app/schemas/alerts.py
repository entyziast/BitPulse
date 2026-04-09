from pydantic import BaseModel
from enum import Enum


class AlertType(str, Enum):
    PRICE_THRESHOLD = "price_threshold"
    #PRICE_PERCENT_CHANGE = "price_percent"


class AlertOperator(str, Enum):
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='


class AlertBase(BaseModel):

    name: str | None = None
    symbol: str
    alert_type: AlertType
    alert_operator: AlertOperator

    model_config = {"from_attributes": True}


class AlertCreate(AlertBase):
    value: int

class AlertShow(AlertBase):
    target_value: int