from pydantic import BaseModel, EmailStr, Field
import datetime

class BaseUser(BaseModel):
    username: str = Field(..., min_length=4, max_length=16)
    email: EmailStr

    model_config = {"from_attributes": True}


class CreateUser(BaseUser):
    password: str = Field(..., min_length=6, max_length=32)


class ShowUser(BaseUser):
    id: int
    created_at: datetime.datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str