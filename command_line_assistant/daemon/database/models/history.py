"""Module containing SQLAlchemy models for the daemon."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from command_line_assistant.daemon.database.models.base import GUID, BaseModel


class HistoryModel(BaseModel):
    """SQLAlchemy model for history table that maps to HistoryEntry dataclass."""

    __tablename__ = "history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    interaction_id = Column(GUID(), ForeignKey("interaction.id"), nullable=False)
    interaction = relationship("InteractionModel", backref="history")


class InteractionModel(BaseModel):
    """SQLAlchemy model for interaction table."""

    __tablename__ = "interaction"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text)
    query_role = Column(String(4), default="user")
    response_text = Column(Text)
    response_role = Column(String(9), default="assistant")
    response_tokens = Column(Integer, default=0)
    os_distribution = Column(String(4), default="RHEL")
    os_version = Column(String(100), nullable=False)
    os_arch = Column(String(7), nullable=False)
