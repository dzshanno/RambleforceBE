from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import User, Registration, Event
from app.utils.auth import get_current_active_user
from app.schemas.auth import User as UserSchema

router = APIRouter()

@router.get("/me/registrations", response_model=List[dict])
async def get_my_registrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    registrations = db.query(Registration).filter(
        Registration.user_id == current_user.id
    ).all()
    return registrations

@router.post("/{event_id}/register")
async def register_for_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    existing_registration = db.query(Registration).filter(
        Registration.user_id == current_user.id,
        Registration.event_id == event_id
    ).first()
    
    if existing_registration:
        raise HTTPException(status_code=400, detail="Already registered for this event")
    
    # Create new registration
    registration = Registration(
        user_id=current_user.id,
        event_id=event_id,
        status="registered"
    )
    
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration
