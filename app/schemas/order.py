# app/schemas/order.py
from pydantic import constr
from typing import List, Optional, Dict, Literal
from datetime import datetime
from app.schemas.base import BaseSchema


# Base schemas
class OrderItemBase(BaseSchema):
    merchandise_id: int
    quantity: int


class OrderBase(BaseSchema):
    total_amount: float
    status: str


# Create schemas
class OrderItemCreate(OrderItemBase):
    pass


class OrderCreate(BaseSchema):
    items: List[OrderItemCreate]


# Update schemas
class OrderUpdate(BaseSchema):
    status: Literal["pending", "paid", "shipped", "delivered", "cancelled"]


# Response schemas
class OrderItemResponse(OrderItemBase):
    id: int
    price: float
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    updated_by_id: int


class OrderResponse(BaseSchema):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    updated_by_id: int


# Detail schemas
class OrderItemDetail(OrderItemResponse):
    merchandise_id: int
    merchandise_name: str
    merchandise_price: float
    quantity: int
    price: float


class OrderWithItems(OrderResponse):
    items: List[OrderItemResponse]


class OrderDetailResponse(OrderResponse):
    items: List[OrderItemDetail]
    user_email: str
    user_full_name: str


#  Summary schemas
class OrderSummary(BaseSchema):
    id: int
    status: str
    total_amount: float
    item_count: int
    created_at: datetime
    updated_by_id: int


# Statistics schemas
class OrderStats(BaseSchema):
    total_orders: int
    total_revenue: float
    average_order_value: float
    orders_by_status: Dict[str, int]
