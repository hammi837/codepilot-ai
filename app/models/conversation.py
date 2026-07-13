from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base, TimestampMixin


class ConversationStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ConversationStatus.active.value
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id"
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)   # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized sources

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
