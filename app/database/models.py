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
    func,
)
from sqlalchemy.orm import relationship, declarative_base
import enum

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
    company = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # nullable for first admin
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Self-referential relationships for audit
    created_by_user = relationship(
        "User", remote_side=[id], foreign_keys=[created_by_id]
    )
    updated_by_user = relationship(
        "User", remote_side=[id], foreign_keys=[updated_by_id]
    )

    # Reverse relationships for users created/updated by this user
    users_created = relationship(
        "User",
        back_populates="created_by_user",
        foreign_keys=[created_by_id],
        remote_side=[created_by_id],
    )
    users_updated = relationship(
        "User",
        back_populates="updated_by_user",
        foreign_keys=[updated_by_id],
        remote_side=[updated_by_id],
    )

    # Standard relationships
    registrations = relationship("Registration", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    orders = relationship("Order", back_populates="user")
    events_created = relationship(
        "Event", back_populates="created_by_user", foreign_keys="Event.created_by_id"
    )
    events_updated = relationship(
        "Event", back_populates="updated_by_user", foreign_keys="Event.updated_by_id"
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    date = Column(DateTime)
    location = Column(String)
    capacity = Column(Integer)
    price = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    registrations = relationship("Registration", back_populates="event")
    photos = relationship("Photo", back_populates="event")
    created_by_user = relationship(
        "User", back_populates="events_created", foreign_keys=[created_by_id]
    )
    updated_by_user = relationship(
        "User", back_populates="events_updated", foreign_keys=[updated_by_id]
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    status = Column(Enum(RegistrationStatus))
    registration_date = Column(DateTime, server_default=func.now())
    payment_status = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])


class Merchandise(Base):
    __tablename__ = "merchandise"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])
    order_items = relationship("OrderItem", back_populates="merchandise")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String)  # pending, paid, shipped, delivered, cancelled
    order_date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    merchandise_id = Column(Integer, ForeignKey("merchandise.id"))
    quantity = Column(Integer)
    price = Column(Float)  # Price at time of order
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    order = relationship("Order", back_populates="items")
    merchandise = relationship("Merchandise", back_populates="order_items")
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="comments", foreign_keys=[user_id])
    replies = relationship("Comment", backref="parent", remote_side=[id])
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    url = Column(String)
    caption = Column(String, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    event = relationship("Event", back_populates="photos")
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])


class AIQuestion(Base):
    __tablename__ = "ai_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # The user who asked the question
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_id])
