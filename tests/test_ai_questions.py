# tests/test_ai_questions.py
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.database.models import User, AIQuestion
from app.utils.auth import create_access_token
from sqlalchemy.sql import func
from app.utils.logging_config import setup_logging

# Set up logging
logger = logger = setup_logging()


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin@example.com",
        hashed_password="hashed_password",
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.email})


@pytest.fixture
def mock_ai_service():
    with patch("app.utils.ai_service.AIService") as MockService:
        service_instance = MagicMock()
        # Remove AsyncMock for get_answer
        service_instance.get_answer = MagicMock(return_value="Mocked AI response")
        MockService.return_value = service_instance
        yield service_instance


@pytest.mark.asyncio
async def test_create_ai_question_anonymous(client, mock_ai_service, db_session):
    response = client.post(
        "/api/v1/ai/ask", json={"question": "What is Rambleforce25?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is Rambleforce25?"
    assert data["answer"] == "Mocked AI response"

    # Verify question was saved in database
    db_question = db_session.query(AIQuestion).first()
    assert db_question is not None
    assert db_question.question == "What is Rambleforce25?"
    assert db_question.answer == "Mocked AI response"
    assert db_question.user_id is None


@pytest.mark.asyncio
async def test_create_ai_question_authenticated(
    client, mock_ai_service, user_token, test_user, db_session
):
    response = client.post(
        "/api/v1/ai/ask",
        json={"question": "What is Rambleforce25?"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mocked AI response"
    assert data["user_id"] == test_user.id

    # Verify question was saved with correct user ID
    db_question = db_session.query(AIQuestion).first()
    assert db_question.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_all_questions_admin(client, admin_token, db_session):
    # Create test questions
    questions = []
    for i in range(3):
        question = AIQuestion(
            question=f"Test question {i}",
            answer=f"Test answer {i}",
            created_at=func.now(),
        )
        db_session.add(question)
        questions.append(question)
    db_session.commit()

    response = client.get(
        "/api/v1/ai/questions", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(q["question"].startswith("Test question") for q in data)


@pytest.mark.asyncio
async def test_get_my_questions(client, user_token, test_user, db_session):
    # Create user's questions
    for i in range(2):
        question = AIQuestion(
            question=f"User question {i}",
            answer=f"User answer {i}",
            user_id=test_user.id,
            created_at=func.now(),
        )
        db_session.add(question)

    # Create another user's question
    other_question = AIQuestion(
        question="Other question",
        answer="Other answer",
        user_id=None,
        created_at=func.now(),
    )
    db_session.add(other_question)
    db_session.commit()

    response = client.get(
        "/api/v1/ai/my-questions", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("User question" in q["question"] for q in data)


@pytest.mark.asyncio
async def test_ai_service_error(client, mock_ai_service):
    # Configure mock to raise an exception
    mock_ai_service.get_answer.side_effect = Exception("AI Service Error")

    response = client.post(
        "/api/v1/ai/ask", json={"question": "What is Rambleforce25?"}
    )

    assert response.status_code == 500
    assert "Error getting AI response" in response.json()["detail"]


@pytest.mark.asyncio
async def test_pagination(client, admin_token, db_session):
    # Create 15 test questions
    for i in range(15):
        question = AIQuestion(
            question=f"Test question {i}",
            answer=f"Test answer {i}",
            created_at=func.now(),
        )
        db_session.add(question)
    db_session.commit()

    # Test default pagination
    response = client.get(
        "/api/v1/ai/questions", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 10

    # Test custom pagination
    response = client.get(
        "/api/v1/ai/questions?skip=10&limit=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 5
