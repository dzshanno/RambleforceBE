from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import Event as EventModel, User
from app.utils.auth import get_current_active_user
from app.schemas.event import Event, EventCreate, EventResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[EventResponse])
async def get_events(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    events = db.query(EventModel).offset(skip).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to create events")

    logger.debug(f"Creating event with data: {event.dict()}")

    db_event = EventModel(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update events")

    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_update.dict().items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/{event_id}", response_model=dict)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete events")

    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()
    return {"message": f"Event {event_id} deleted successfully"}
