# app/routers/ai_questions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.database.models import AIQuestion, User
from app.schemas.ai_question import AIQuestionCreate, AIQuestionResponse, AIQuestionInDB
from app.utils.auth import get_current_active_user_or_none
from app.utils.ai_service import AIService
from app.utils.config import settings
from app.utils.logging_config import setup_logging

# Set up logging
logger = setup_logging()

router = APIRouter()


# Create AIService as a dependency
def get_ai_service():
    return AIService()


@router.post("/ask", response_model=AIQuestionResponse)
async def create_ai_question(
    question: AIQuestionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user_or_none),
    ai_service: AIService = Depends(get_ai_service),
):
    """Create a new AI question and get response"""
    try:
        # Pass the database session to get_answer
        answer = await ai_service.get_answer(
            question.question, db=db, user_id=current_user.id if current_user else None
        )

        return AIQuestionResponse(
            question=question.question,
            answer=answer,
            user_id=current_user.id if current_user else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting AI response: {str(e)}"
        )


@router.get("/questions", response_model=List[AIQuestionInDB])
async def get_ai_questions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    """Get list of AI questions"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only admin users can view all questions"
        )

    questions = (
        db.query(AIQuestion)
        .order_by(AIQuestion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return questions


@router.get("/my-questions", response_model=List[AIQuestionInDB])
async def get_user_ai_questions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    """Get list of user's AI questions"""
    if not current_user:
        raise HTTPException(
            status_code=401, detail="Authentication required to view your questions"
        )

    questions = (
        db.query(AIQuestion)
        .filter(AIQuestion.user_id == current_user.id)
        .order_by(AIQuestion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return questions
