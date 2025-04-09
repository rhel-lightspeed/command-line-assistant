"""Module containing SQLAlchemy models for the history."""

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from command_line_assistant.daemon.database.models.base import GUID, BaseModel


class HistoryModel(BaseModel):
    """SQLAlchemy model for history table that maps to HistoryEntry dataclass."""

    __tablename__ = "history"

    user_id: Mapped[GUID] = mapped_column(GUID(), nullable=False)
    chat_id: Mapped[GUID] = mapped_column(GUID(), ForeignKey("chat.id"), nullable=False)

    interactions = relationship("InteractionModel", lazy="subquery", backref="history")
    chats = relationship("ChatModel", lazy="subquery", backref="history")


class InteractionModel(BaseModel):
    """SQLAlchemy model for interaction table."""

    __tablename__ = "interaction"

    history_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("history.id"), nullable=False
    )
    question: Mapped[Text] = mapped_column(Text, nullable=False)
    response: Mapped[Text] = mapped_column(Text, nullable=False)
