"""Creation Draft session model for crash/restart recovery."""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base

class CreationDraft(Base):
    __tablename__ = "creation_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False)
    
    state: Mapped[str] = mapped_column(String(64), default="WAITING_TITLE")
    pending_media_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pending_media_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="draft")
    quiz: Mapped["Quiz"] = relationship("Quiz")
