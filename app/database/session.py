# Contains the database session configuration

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.utils.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
