"""
PFOR Database — SQLAlchemy Models
Defines the User and StrategyRequest ORM models for the production PostgreSQL setup.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from pfor.db.database import Base


class User(Base):
    """Registered platform user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_subscribed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strategy_requests = relationship(
        "StrategyRequest",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class StrategyRequest(Base):
    """AI-generated business strategy request and result."""

    __tablename__ = "strategy_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    prompt_text = Column(Text, nullable=False)
    language = Column(String(10), default="ru", nullable=False)
    status = Column(String(32), default="processing", nullable=False)
    result_markdown = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="strategy_requests")

    def __repr__(self) -> str:
        return f"<StrategyRequest id={self.id} user_id={self.user_id} status={self.status}>"
