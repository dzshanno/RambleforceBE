from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import Merchandise, Order, OrderItem, User
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_merchandise(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    items = db.query(Merchandise).offset(skip).limit(limit).all()
    return items

@router.post("/order", response_model=dict)
async def create_order(
    items: List[dict],  # List of {merchandise_id: int, quantity: int}
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Calculate total amount and verify stock
    total_amount = 0
    order_items = []
    
    for item in items:
        merchandise = db.query(Merchandise).filter(
            Merchandise.id == item["merchandise_id"]
        ).first()
        
        if not merchandise:
            raise HTTPException(status_code=404, detail=f"Merchandise {item['merchandise_id']} not found")
        
        if merchandise.stock < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {merchandise.name}")
        
        total_amount += merchandise.price * item["quantity"]
        order_items.append({"merchandise": merchandise, "quantity": item["quantity"]})
    
    # Create order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="pending"
    )
    db.add(order)
    db.commit()
    
    # Create order items and update stock
    for item in order_items:
        order_item = OrderItem(
            order_id=order.id,
            merchandise_id=item["merchandise"].id,
            quantity=item["quantity"],
            price=item["merchandise"].price
        )
        item["merchandise"].stock -= item["quantity"]
        db.add(order_item)
    
    db.commit()
    db.refresh(order)
    return order
