"""Question database model."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_poll_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option_id: Mapped[int] = mapped_column(Integer, nullable=False)  # original option index (0-based)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pre-question media
    media_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # photo, video, document, animation, text
    
    position: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Future-ready fields (extensible)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latex_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    option_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    options: Mapped[List["Option"]] = relationship("Option", back_populates="question", order_by="Option.option_index", cascade="all, delete-orphan", lazy="selectin")
