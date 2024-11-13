from pydantic import EmailStr
from typing import Optional
from .base import BaseSchema


class Token(BaseSchema):
    access_token: str
    token_type: str


class TokenData(BaseSchema):
    email: Optional[str] = None


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str
    company: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool = True
    is_admin: bool = False


class UserInDB(User):
    hashed_password: str
