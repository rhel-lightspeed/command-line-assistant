"""Module containing SQLAlchemy models for the chat session."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from command_line_assistant.daemon.database.models.base import GUID, BaseModel


class ChatModel(BaseModel):
    """SQLAlchemy model for chat table."""

    __tablename__ = "chat"

    user_id: Mapped[GUID] = mapped_column(GUID(), nullable=False)
    name: Mapped[int] = mapped_column(String(25), nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
