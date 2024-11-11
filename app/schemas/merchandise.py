from pydantic import BaseModel
from typing import Optional, List

class MerchandiseBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    image_url: Optional[str] = None

class MerchandiseCreate(MerchandiseBase):
    pass

class Merchandise(MerchandiseBase):
    id: int

    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    merchandise_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
