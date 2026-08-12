from datetime import date

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters")
        return value


class UserOut(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TripCreate(BaseModel):
    destination: str
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class TripOut(BaseModel):
    id: int
    destination: str
    start_date: date
    end_date: date

    model_config = {"from_attributes": True}


class ItineraryItemCreate(BaseModel):
    title: str
    day: date


class ItineraryItemOut(BaseModel):
    id: int
    title: str
    day: date

    model_config = {"from_attributes": True}
