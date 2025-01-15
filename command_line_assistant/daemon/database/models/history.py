"""Module containing SQLAlchemy models for the daemon."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from command_line_assistant.daemon.database.models.base import BaseModel


class HistoryModel(BaseModel):
    """SQLAlchemy model for history table that maps to HistoryEntry dataclass."""

    __tablename__ = "history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    interaction_id = Column(
        UUID(as_uuid=True), ForeignKey("interaction.id"), nullable=False
    )
    interaction = relationship("InteractionModel", backref="history")


class InteractionModel(BaseModel):
    """SQLAlchemy model for interaction table."""

    __tablename__ = "interaction"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(String)
    query_role = Column(String, default="user")
    response_text = Column(String)
    response_role = Column(String, default="assistant")
    response_tokens = Column(Integer, default=0)
    os_distribution = Column(String, default="RHEL")
    os_version = Column(String, nullable=False)
    os_arch = Column(String, nullable=False)
