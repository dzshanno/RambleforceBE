from anthropic import Anthropic
from app.utils.config import settings
from app.database.models import AIQuestion
from typing import Optional
from sqlalchemy.orm import Session
from app.utils.logging_config import setup_logging

logger = setup_logging()


class AIService:
    def __init__(self, client=None):
        self.client = client or Anthropic(api_key=settings.ANTHROPIC_API_KEY)
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

    def get_answer(
        self, question: str, db: Session, user_id: Optional[int] = None
    ) -> str:
        """
        Get answer from AI service and save to database

        Args:
            question: The question to ask
            db: Database session
            user_id: Optional user ID for tracking who asked the question

        Returns:
            str: The AI's response

        Raises:
            Exception: If there is an error getting the response or saving to database
        """
        try:
            logger.info(f"Getting AI response for question: {question}")
            message = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,  # Use from settings for consistency
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context: {self.context}\n\nQuestion: {question}",
                    }
                ],
            )

            answer = message.content[0].text

            # Store the Q&A in the database
            ai_question = AIQuestion(
                question=question,
                answer=answer,
                user_id=user_id,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
            db.add(ai_question)
            db.commit()
            db.refresh(ai_question)  # Refresh to get the complete object

            logger.info("Successfully saved AI question and response")
            return answer

        except Exception as e:
            logger.error(f"Error in AI service: {str(e)}")
            db.rollback()  # Rollback transaction on error
            raise  # Re-raise the original exception with full context
