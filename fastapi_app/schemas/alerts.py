from pydantic import BaseModel, field_validator, ValidationInfo
from enum import Enum
import datetime

class AlertType(str, Enum):
    ALWAYS_TRIGGER = "always_trigger"
    PRICE_THRESHOLD = "price_threshold"
    #PRICE_PERCENT_CHANGE = "price_percent"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    INACTIVE = "inactive"

class AlertOperator(str, Enum):
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='


class AlertBase(BaseModel):

    name: str | None = None
    alert_type: AlertType
    alert_operator: AlertOperator


    model_config = {"from_attributes": True}


class AlertCreate(AlertBase):
    symbol: str
    value: float

    @field_validator('value')
    def validate_value(cls, v: float, info: ValidationInfo) -> float:
        if info.data.get('alert_type') == AlertType.PRICE_THRESHOLD and v <= 0:
            raise ValueError('Value must be greater than 0 for price threshold alerts')
        return v

class AlertShow(AlertBase):
    id: int
    alert_status: AlertStatus
    target_value: float
    created_at: datetime.datetime
    triggered_at: datetime.datetime | None = None