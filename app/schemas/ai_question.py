# app/schemas/ai_question.py
from datetime import datetime
from typing import Optional
from .base import BaseSchema


class AIQuestionBase(BaseSchema):
    question: str


class AIQuestionCreate(AIQuestionBase):
    pass


class AIQuestionResponse(AIQuestionBase):
    answer: str
    user_id: Optional[int] = None
    created_at: datetime


class AIQuestionInDB(AIQuestionResponse):
    id: int
    updated_at: datetime
    created_by_id: Optional[int]
    updated_by_id: Optional[int]
