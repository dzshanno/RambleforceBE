from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models import Comment, User
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_comments(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    comments = db.query(Comment).filter(
        Comment.parent_id == None  # Only get top-level comments
    ).offset(skip).limit(limit).all()
    return comments

@router.get("/{comment_id}/replies", response_model=List[dict])
async def get_replies(
    comment_id: int,
    db: Session = Depends(get_db)
):
    replies = db.query(Comment).filter(
        Comment.parent_id == comment_id
    ).all()
    return replies

@router.post("/", response_model=dict)
async def create_comment(
    comment: dict,  # {content: str, parent_id: Optional[int]}
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if comment.get("parent_id"):
        parent_comment = db.query(Comment).filter(
            Comment.id == comment["parent_id"]
        ).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    db_comment = Comment(
        user_id=current_user.id,
        content=comment["content"],
        parent_id=comment.get("parent_id")
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment
