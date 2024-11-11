from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime, timezone
from sqlalchemy.sql import func

Base = declarative_base()


class RegistrationStatus(enum.Enum):
    INTERESTED = "interested"
    REGISTERED = "registered"
    WAITLISTED = "waitlisted"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    company = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    registrations = relationship("Registration", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    status = Column(Enum(RegistrationStatus))
    registration_date = Column(DateTime, default=func.now())
    payment_status = Column(String)

    # Relationships
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    date = Column(DateTime)
    location = Column(String)
    capacity = Column(Integer)
    price = Column(Float)

    # Relationships
    registrations = relationship("Registration", back_populates="event")
    photos = relationship("Photo", back_populates="event")


class Merchandise(Base):
    __tablename__ = "merchandise"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer)
    image_url = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String)
    order_date = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    merchandise_id = Column(Integer, ForeignKey("merchandise.id"))
    quantity = Column(Integer)
    price = Column(Float)

    # Relationships
    order = relationship("Order", back_populates="items")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="comments")
    replies = relationship("Comment")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    url = Column(String)
    caption = Column(String)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    event = relationship("Event", back_populates="photos")


class AIQuestion(Base):
    __tablename__ = "ai_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
