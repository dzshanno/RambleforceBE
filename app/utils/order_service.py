# app/utils/order_service.py
from sqlalchemy.orm import Session
from app.database.models import Order, OrderItem, Merchandise
from app.schemas.order import OrderCreate, OrderItemCreate
from fastapi import HTTPException
from typing import List, Tuple
from app.utils.logging_config import setup_logging

logger = setup_logging()


class OrderService:
    @staticmethod
    async def validate_order_items(
        db: Session, items: List[OrderItemCreate]
    ) -> List[Tuple[Merchandise, int, float]]:
        """
        Validate order items and return list of (merchandise, quantity, price) tuples
        """
        order_items = []
        total_amount = 0

        for item in items:
            merchandise = db.query(Merchandise).get(item.merchandise_id)
            if not merchandise:
                raise HTTPException(
                    status_code=404,
                    detail=f"Merchandise with id {item.merchandise_id} not found",
                )

            if merchandise.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {merchandise.name}. Available: {merchandise.stock}",
                )

            item_total = merchandise.price * item.quantity
            total_amount += item_total
            order_items.append((merchandise, item.quantity, item_total))

        return order_items

    @staticmethod
    async def create_order_items(
        db: Session,
        order_id: int,
        items: List[Tuple[Merchandise, int, float]],
        user_id: int,
    ):
        """
        Create order items and update merchandise stock
        """
        for merchandise, quantity, price in items:
            order_item = OrderItem(
                order_id=order_id,
                merchandise_id=merchandise.id,
                quantity=quantity,
                price=price,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
            db.add(order_item)

            # Update stock
            merchandise.stock -= quantity

    @staticmethod
    async def cancel_order(db: Session, order: Order, user_id: int):
        """
        Cancel order and restore stock
        """
        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        # Restore stock
        for item in order.items:
            merchandise = item.merchandise
            merchandise.stock += item.quantity

        order.status = "cancelled"
        order.updated_by_id = user_id
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    async def get_order_summary(order: Order) -> dict:
        """
        Get order summary including items and totals
        """
        items_summary = []
        for item in order.items:
            items_summary.append(
                {
                    "name": item.merchandise.name,
                    "quantity": item.quantity,
                    "price_per_item": item.merchandise.price,
                    "total_price": item.price,
                }
            )

        return {
            "order_id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "items": items_summary,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }
