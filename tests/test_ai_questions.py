# tests/test_ai_questions.py
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
from app.database.models import User, AIQuestion
from app.utils.auth import create_access_token
from app.utils.logging_config import setup_logging
from app.routers.ai_questions import get_ai_service
from app.main import app
from datetime import datetime, timezone

# Set up logging
logger = setup_logging()


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service that returns a predefined response"""
    mock_service = MagicMock()

    def mock_get_answer(question: str, db, user_id=None):
        # Simulate the actual service's database operations
        ai_question = AIQuestion(
            question=question,
            answer="Mocked AI response",
            user_id=user_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(ai_question)
        db.commit()
        return "Mocked AI response"

    mock_service.get_answer = MagicMock(side_effect=mock_get_answer)
    return mock_service


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


def test_create_ai_question_anonymous(client, mock_ai_service, db_session):
    # Override the AI service dependency
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    response = client.post(
        "/api/v1/ai/ask", json={"question": "What is Rambleforce25?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is Rambleforce25?"
    assert data["answer"] == "Mocked AI response"

    # Verify the mock was called correctly
    mock_ai_service.get_answer.assert_called_once_with(
        "What is Rambleforce25?", db=db_session, user_id=None
    )

    # Verify question was saved in database
    db_question = db_session.query(AIQuestion).first()
    assert db_question is not None
    assert db_question.question == "What is Rambleforce25?"
    assert db_question.answer == "Mocked AI response"
    assert db_question.user_id is None

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_ai_question_authenticated(
    client, mock_ai_service, user_token, test_user, db_session
):
    # Override the AI service dependency
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    response = client.post(
        "/api/v1/ai/ask",
        json={"question": "What is Rambleforce25?"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mocked AI response"
    assert data["user_id"] == test_user.id

    # Verify the mock was called correctly
    mock_ai_service.get_answer.assert_called_once_with(
        "What is Rambleforce25?", db=db_session, user_id=test_user.id
    )

    # Verify question was saved with correct user ID
    logger.debug(f"Checking database for question by user ID: {test_user.id}")
    db_question = db_session.query(AIQuestion).first()
    assert db_question.user_id == test_user.id

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_ai_service_error(client, mock_ai_service):
    # Override the AI service dependency
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service

    # Configure mock to raise an exception
    mock_ai_service.get_answer.side_effect = Exception("AI Service Error")

    response = client.post(
        "/api/v1/ai/ask", json={"question": "What is Rambleforce25?"}
    )

    assert response.status_code == 500
    assert "Error getting AI response" in response.json()["detail"]

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_get_all_questions_admin(client, admin_token, db_session):
    # Create test questions
    questions = []
    for i in range(3):
        question = AIQuestion(
            question=f"Test question {i}",
            answer=f"Test answer {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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


def test_get_my_questions(client, user_token, test_user, db_session):
    # Create user's questions
    for i in range(2):
        question = AIQuestion(
            question=f"User question {i}",
            answer=f"User answer {i}",
            user_id=test_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
            updated_by_id=test_user.id,
        )
        db_session.add(question)

    # Create another user's question
    other_question = AIQuestion(
        question="Other question",
        answer="Other answer",
        user_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
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


def test_pagination(client, admin_token, db_session):
    # Create 15 test questions
    for i in range(15):
        question = AIQuestion(
            question=f"Test question {i}",
            answer=f"Test answer {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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
