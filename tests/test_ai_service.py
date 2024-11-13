# tests/test_ai_service.py
from unittest.mock import MagicMock
import pytest
from app.utils.ai_service import AIService
from app.utils.logging_config import setup_logging
from app.database.models import User, AIQuestion
from sqlalchemy.orm import Session

logger = setup_logging()


class MockMessage:
    def __init__(self, text):
        self.text = text


class MockResponse:
    def __init__(self, text="Mocked AI response"):
        self.content = [MockMessage(text)]


@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    client.messages.create = MagicMock(return_value=MockResponse())
    return client


def test_get_answer_with_user(mock_anthropic_client, test_users, db_session):
    # First, let's verify what users exist in the database
    all_users = db_session.query(User).all()
    logger.debug("All users in database:")
    for user in all_users:
        logger.debug(f"User ID: {user.id}, Email: {user.email}")

    # Get the regular user from test_users
    regular_user = test_users["user"]
    logger.debug(
        f"Selected test user - ID: {regular_user.id}, Email: {regular_user.email}"
    )

    service = AIService(client=mock_anthropic_client)
    answer = service.get_answer(
        "Test question?", db=db_session, user_id=regular_user.id
    )
    assert answer == "Mocked AI response"

    # Verify the mock was called correctly
    mock_anthropic_client.messages.create.assert_called_once()
    call_args = mock_anthropic_client.messages.create.call_args[1]
    assert "Test question?" in str(call_args["messages"])

    # Verify the database entry
    db_question = db_session.query(AIQuestion).first()
    assert db_question is not None
    assert (
        db_question.user_id == regular_user.id
    ), f"Question user_id {db_question.user_id} doesn't match test user id {regular_user.id}"
    assert db_question.question == "Test question?"
    assert db_question.answer == "Mocked AI response"


def test_get_answer_without_user(mock_anthropic_client, db_session):
    service = AIService(client=mock_anthropic_client)
    answer = service.get_answer("Test question?", db=db_session, user_id=None)
    assert answer == "Mocked AI response"

    # Verify the mock was called correctly
    mock_anthropic_client.messages.create.assert_called_once()
    call_args = mock_anthropic_client.messages.create.call_args[1]
    assert "Test question?" in str(call_args["messages"])

    # Verify the database entry
    db_question = db_session.query(AIQuestion).first()
    assert db_question is not None
    assert db_question.user_id is None
    assert db_question.question == "Test question?"
    assert db_question.answer == "Mocked AI response"


def test_database_state(mock_anthropic_client, test_users, db_session):
    """Debug test to examine database state"""
    # Check Users table
    all_users = db_session.query(User).all()
    logger.debug("\nDatabase state - Users:")
    for user in all_users:
        logger.debug(
            f"User ID: {user.id}, Email: {user.email}, Active: {user.is_active}"
        )

    # Check if our test user is properly accessible
    regular_user = test_users["user"]
    logger.debug(f"\nTest user details:")
    logger.debug(f"ID: {regular_user.id}")
    logger.debug(f"Email: {regular_user.email}")
    logger.debug(f"Active: {regular_user.is_active}")

    # Verify the user exists in a fresh query
    db_user = db_session.query(User).get(regular_user.id)
    assert db_user is not None, f"Could not find user with ID {regular_user.id}"


def test_ai_service_error(mock_anthropic_client, db_session):
    # Configure mock to raise an exception
    mock_anthropic_client.messages.create.side_effect = Exception("AI Service Error")

    service = AIService(client=mock_anthropic_client)

    with pytest.raises(Exception) as exc_info:
        service.get_answer("Test question?", db=db_session, user_id=None)

    assert "AI Service Error" in str(exc_info.value)

    # Verify no question was saved in the database
    db_question = db_session.query(AIQuestion).first()
    assert db_question is None
