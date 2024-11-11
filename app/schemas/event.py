from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventBase(BaseModel):
    title: str
    description: str
    date: datetime
    location: str
    capacity: int
    price: float


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # This enables ORM model -> Pydantic model conversion


class EventResponse(Event):
    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
