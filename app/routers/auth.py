from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.utils.auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    get_current_active_user,
    get_current_active_user_or_none,
    get_current_user_optional,
    OAuth2PasswordBearerOptional,
)
from app.schemas.auth import Token, UserCreate, User, UserLogin
from app.database.models import User as UserModel
from jose import JWTError, jwt
from app.utils.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/signup", response_model=User)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_active_user_or_none),
):
    logger.debug(f"Attempting to create user with email: {user.email}")

    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only allow admin users to create new users after initial setup
    if db.query(UserModel).count() > 0 and (
        not current_user or not current_user.is_admin
    ):
        raise HTTPException(
            status_code=403, detail="Only admin users can create new users"
        )

    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        company=user.company,
        created_by_id=current_user.id if current_user else None,
        updated_by_id=current_user.id if current_user else None,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.debug(f"Successfully created user with id: {db_user.id}")
    return db_user


@router.post("/login", response_model=Token)
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    logger.debug(f"Login attempt for user: {user_data.email}")

    user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    logger.debug(f"User found: {user is not None}")

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.debug("Successfully created access token")

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logger.debug(f"Token endpoint called with username: {form_data.username}")

    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    logger.debug(f"User found: {user is not None}")

    if user:
        password_correct = verify_password(form_data.password, user.hashed_password)
        logger.debug(f"Password verification result: {password_correct}")

        if password_correct:
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            logger.debug("Successfully created access token")
            return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user
