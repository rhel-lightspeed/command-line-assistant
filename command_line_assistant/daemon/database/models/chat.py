"""Module containing SQLAlchemy models for the chat session."""

from sqlalchemy import Column, String, Text

from command_line_assistant.daemon.database.models.base import GUID, BaseModel


class ChatModel(BaseModel):
    """SQLAlchemy model for chat table."""

    __tablename__ = "chat"

    user_id = Column(GUID(), nullable=False)  # type: ignore[var-annotated]
    name = Column(String(25), nullable=False)  # type: ignore[var-annotated]
    description = Column(Text, nullable=True)  # type: ignore[var-annotated]
