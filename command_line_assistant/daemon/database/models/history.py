"""Module containing SQLAlchemy models for the history."""

from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import relationship

from command_line_assistant.daemon.database.models.base import GUID, BaseModel


class HistoryModel(BaseModel):
    """SQLAlchemy model for history table that maps to HistoryEntry dataclass."""

    __tablename__ = "history"

    user_id = Column(GUID(), nullable=False)
    chat_id = Column(GUID(), ForeignKey("chat.id"), nullable=False)

    interactions = relationship("InteractionModel", lazy="subquery", backref="history")
    chats = relationship("ChatModel", lazy="subquery", backref="history")


class InteractionModel(BaseModel):
    """SQLAlchemy model for interaction table."""

    __tablename__ = "interaction"

    history_id = Column(GUID(), ForeignKey("history.id"), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
