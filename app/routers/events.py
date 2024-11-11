from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import Event, User
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_events(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    events = db.query(Event).offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=dict)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=dict)
async def create_event(
    event: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to create events")
    
    db_event = Event(**event)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
