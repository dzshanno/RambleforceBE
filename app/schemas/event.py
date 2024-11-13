from datetime import datetime
from .base import BaseSchema


class EventBase(BaseSchema):
    """Base Event schema with common attributes"""

    title: str
    description: str
    date: datetime
    location: str
    capacity: int
    price: float


class EventCreate(EventBase):
    """Schema for creating a new event"""

    pass


class Event(EventBase):
    """Schema for event with database fields"""

    id: int
    created_at: datetime


class EventResponse(Event):
    """Schema for event responses"""

    pass
