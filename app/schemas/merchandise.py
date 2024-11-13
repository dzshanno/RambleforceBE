from typing import Optional, List
from .base import BaseSchema


class MerchandiseBase(BaseSchema):
    name: str
    description: str
    price: float
    stock: int
    image_url: Optional[str] = None


class MerchandiseCreate(MerchandiseBase):
    pass


class Merchandise(MerchandiseBase):
    id: int


class OrderItemCreate(BaseSchema):
    merchandise_id: int
    quantity: int


class OrderCreate(BaseSchema):
    items: List[OrderItemCreate]
