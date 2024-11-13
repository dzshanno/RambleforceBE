# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from app.database.session import get_db
from app.database.models import Order, OrderItem, Merchandise, User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    OrderWithItems,
    OrderDetailResponse,
    OrderSummary,
    OrderStats,
    OrderItemDetail,
    OrderItemCreate,
)
from app.utils.auth import get_current_active_user
from app.utils.logging_config import setup_logging

logger = setup_logging()
router = APIRouter()


def validate_order_items(db: Session, items: List[OrderItemCreate]):
    """Validate all items in the order and return total amount and validated items"""
    total_amount = 0
    validated_items = []

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
                detail=f"Insufficient stock for {merchandise.name}. Available: {merchandise.stock}, Requested: {item.quantity}",
            )

        item_total = merchandise.price * item.quantity
        total_amount += item_total
        validated_items.append((merchandise, item.quantity, item_total))

    return total_amount, validated_items


@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new order with items"""
    try:
        total_amount, validated_items = validate_order_items(db, order.items)
    except HTTPException as he:
        # Re-raise HTTP exceptions from validation
        raise he
    except Exception as e:
        logger.error(f"Error validating order items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    try:
        # Create order
        db_order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            status="pending",
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(db_order)
        db.flush()  # Get order ID without committing

        # Create order items
        for merchandise, quantity, price in validated_items:
            order_item = OrderItem(
                order_id=db_order.id,
                merchandise_id=merchandise.id,
                quantity=quantity,
                price=price,
                created_by_id=current_user.id,
                updated_by_id=current_user.id,
            )
            db.add(order_item)

            # Update stock
            merchandise.stock -= quantity

        db.commit()
        db.refresh(db_order)
        return db_order

    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the order: {str(e)}",
        )


@router.get("/my-orders", response_model=List[OrderWithItems])
async def get_user_orders(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all orders for the current user"""
    query = db.query(Order).filter(Order.user_id == current_user.id)

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderWithItems)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific order"""
    order = (
        db.query(Order)
        .filter(and_(Order.id == order_id, Order.user_id == current_user.id))
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update order status (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can update order status"
        )

    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update status and audit fields
    previous_status = order.status
    order.status = order_update.status
    order.updated_by_id = current_user.id

    # If order is cancelled, restore stock
    if order_update.status == "cancelled" and previous_status != "cancelled":
        for item in order.items:
            merchandise = item.merchandise
            merchandise.stock += item.quantity

    # If reactivating a cancelled order, deduct stock again
    elif previous_status == "cancelled" and order_update.status != "cancelled":
        logger.info(f"Deducting stock for reactivated order {order_id}")
        for item in order.items:
            merchandise = item.merchandise
            if merchandise.stock < item.quantity:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock to reactivate order: {merchandise.name} requires {item.quantity} units but only {merchandise.stock} available",
                )
            merchandise.stock -= item.quantity
            logger.debug(
                f"Deducted {item.quantity} units from merchandise {merchandise.id}"
            )
    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while updating the order status"
        )


@router.get("/admin/all", response_model=List[OrderWithItems])
async def get_all_orders(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all orders (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can view all orders"
        )

    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/my-orders/summary", response_model=List[OrderSummary])
async def get_user_orders_summary(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a summarized list of user's orders"""
    query = (
        db.query(
            Order.id,
            Order.status,
            Order.total_amount,
            Order.created_at,
            func.count(OrderItem.id).label("item_count"),
        )
        .join(OrderItem)
        .filter(Order.user_id == current_user.id)
        .group_by(Order.id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return [
        OrderSummary(
            id=id,
            status=status,
            total_amount=total_amount,
            item_count=item_count,
            created_at=created_at,
        )
        for id, status, total_amount, created_at, item_count in query.all()
    ]


@router.get("/{order_id}/detail", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed order information including user details"""
    order = (
        db.query(Order)
        .filter(and_(Order.id == order_id, Order.user_id == current_user.id))
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderDetailResponse(
        id=order.id,
        user_id=order.user_id,
        user_email=order.user.email,
        user_full_name=order.user.full_name,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemDetail(
                id=item.id,
                merchandise_id=item.merchandise_id,
                merchandise_name=item.merchandise.name,
                merchandise_price=item.merchandise.price,
                quantity=item.quantity,
                price=item.price,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in order.items
        ],
    )


@router.get("/stats", response_model=OrderStats)
async def get_order_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get order statistics for admin dashboard"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can view order statistics"
        )

    # Get total orders and revenue
    stats = db.query(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total_amount).label("total_revenue"),
    ).first()

    # Get orders by status
    status_counts = (
        db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )

    return OrderStats(
        total_orders=stats[0],
        total_revenue=float(stats[1] or 0),
        average_order_value=float(stats[1] or 0) / stats[0] if stats[0] > 0 else 0,
        orders_by_status={status: count for status, count in status_counts},
    )
