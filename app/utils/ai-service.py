from anthropic import Anthropic
from app.utils.config import settings
from app.database.session import get_db
from app.database.models import AIQuestion
from typing import Optional

class AIService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.context = """
        Rambleforce25 is a Salesforce Netwalking event in the Lake District, UK. 
        It combines networking for Salesforce professionals with walking/hiking activities.
        Key details:
        - Typically attended by around 100 people
        - 1000+ people usually express interest
        - Location: Lake District, UK
        - Activities include: networking, hiking, social events
        - Merchandise available for purchase
        - Accommodation sharing options available
        """

    async def get_answer(self, question: str, user_id: Optional[int] = None) -> str:
        try:
            message = await self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"Context: {self.context}\n\nQuestion: {question}"
                }]
            )
            
            answer = message.content[0].text
            
            # Store the Q&A in the database
            db = next(get_db())
            ai_question = AIQuestion(
                question=question,
                answer=answer,
                user_id=user_id
            )
            db.add(ai_question)
            db.commit()
            
            return answer
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

    async def get_previous_answers(self, question: str) -> Optional[str]:
        """Check if we have previously answered a similar question"""
        db = next(get_db())
        similar_question = db.query(AIQuestion).filter(
            AIQuestion.question.ilike(f"%{question}%")
        ).first()
        
        if similar_question:
            return similar_question.answer
        return None

ai_service = AIService()
