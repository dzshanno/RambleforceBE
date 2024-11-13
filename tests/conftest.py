# tests/conftest.py
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.models import Base, User
from app.database.session import get_db
from app.utils.config import settings
from app.utils.auth import create_access_token, get_password_hash
from app.utils.logging_config import setup_logging
import asyncio

# Set up logging
logger = setup_logging()

# Create test database name by appending _test to original database name
DB_NAME = f"{settings.POSTGRES_DB}_test"
DB_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{DB_NAME}"
POSTGRES_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"

# Define standard test users
TEST_USERS = {
    "admin": {
        "email": "admin@test.com",
        "password": "admin_password",
        "full_name": "Admin User",
        "is_admin": True,
        "company": "Test Corp",
    },
    "user": {
        "email": "user@test.com",
        "password": "user_password",
        "full_name": "Regular User",
        "is_admin": False,
        "company": "Test Corp",
    },
    "inactive": {
        "email": "inactive@test.com",
        "password": "inactive_password",
        "full_name": "Inactive User",
        "is_admin": False,
        "is_active": False,
        "company": "Test Corp",
    },
    "moderator": {
        "email": "moderator@test.com",
        "password": "moderator_password",
        "full_name": "Moderator User",
        "is_admin": False,
        "company": "Test Corp",
    },
}


def pytest_configure(config):
    """Configure custom pytest settings"""
    # Add custom markers
    markers = [
        "asyncio: mark test as async",
        "anthropic: mark test as using real Anthropic API",
        "integration: mark test as integration test",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def clear_database(db_session):
    """Clear all data from database tables"""
    logger.info("Clearing database tables")
    meta = Base.metadata
    for table in reversed(meta.sorted_tables):
        logger.debug(f"Clearing table: {table.name}")
        db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture(scope="function")
def create_test_database():
    """Create test database"""
    logger.info(f"Creating test database: {DB_NAME}")

    # Connect to postgres database to create/drop test database
    postgres_engine = create_engine(POSTGRES_URL)

    # Disconnect all users from test database
    with postgres_engine.connect() as conn:
        conn.execute(text("commit"))
        conn.execute(
            text(
                f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = '{DB_NAME}'
                """
            )
        )
        conn.execute(text("commit"))

        # Drop test database if it exists
        conn.execute(text(f'DROP DATABASE IF EXISTS "{DB_NAME}"'))
        conn.execute(text("commit"))
        logger.info(f"Dropped existing database {DB_NAME}")

        # Create test database
        conn.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
        conn.execute(text("commit"))
        logger.info(f"Created new database {DB_NAME}")

    # Create test database engine and create all tables
    test_engine = create_engine(DB_URL)
    Base.metadata.create_all(test_engine)
    logger.info("Created all database tables")

    yield test_engine

    # Clean up - close connections and drop database
    test_engine.dispose()
    with postgres_engine.connect() as conn:
        conn.execute(text("commit"))
        conn.execute(
            text(
                f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = '{DB_NAME}'
                """
            )
        )
        conn.execute(text("commit"))
        conn.execute(text(f'DROP DATABASE IF EXISTS "{DB_NAME}"'))
        conn.execute(text("commit"))
        logger.info(f"Cleaned up test database {DB_NAME}")
    postgres_engine.dispose()


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_engine(create_test_database):
    """Get test database engine"""
    return create_test_database


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    try:
        clear_database(session)
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient

    return TestClient(app)


def create_test_users(db_session):
    """Create all standard test users"""
    created_users = {}
    for user_type, user_data in TEST_USERS.items():
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            is_admin=user_data.get("is_admin", False),
            is_active=user_data.get("is_active", True),
            company=user_data.get("company"),
        )
        db_session.add(user)
        created_users[user_type] = user

    db_session.commit()
    for user in created_users.values():
        db_session.refresh(user)

    return created_users


@pytest.fixture(scope="function")
def test_users(db_session):
    """Fixture that creates and returns all test users"""
    return create_test_users(db_session)


@pytest.fixture(scope="function")
def admin_user(test_users):
    """Return the admin user"""
    return test_users["admin"]


@pytest.fixture(scope="function")
def regular_user(test_users):
    """Return the regular user"""
    return test_users["user"]


@pytest.fixture(scope="function")
def inactive_user(test_users):
    """Return the inactive user"""
    return test_users["inactive"]


@pytest.fixture(scope="function")
def moderator_user(test_users):
    """Return the moderator user"""
    return test_users["moderator"]


@pytest.fixture(scope="function")
def admin_token(admin_user):
    """Return a valid token for the admin user"""
    return create_access_token(data={"sub": admin_user.email})


@pytest.fixture(scope="function")
def user_token(regular_user):
    """Return a valid token for the regular user"""
    return create_access_token(data={"sub": regular_user.email})


@pytest.fixture(scope="function")
def moderator_token(moderator_user):
    """Return a valid token for the moderator user"""
    return create_access_token(data={"sub": moderator_user.email})


def pytest_configure(config):
    """Configure custom pytest markers"""
    markers = [
        "asyncio: mark test as async",
        "anthropic: mark test as using real Anthropic API",
        "integration: mark test as integration test",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
