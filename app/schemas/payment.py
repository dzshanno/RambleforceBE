# app/schemas/payment.py
from pydantic import BaseModel
from typing import Optional


class PaymentCreate(BaseModel):
    order_id: Optional[int] = None
    registration_id: Optional[int] = None


class PaymentResponse(BaseModel):
    client_secret: str
    payment_id: int
