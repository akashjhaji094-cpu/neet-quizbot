"""Group quiz session, participant, and answer models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base

class GroupQuizSession(Base):
    __tablename__ = "group_quiz_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="WAITING", index=True)  # WAITING, IN_PROGRESS, COMPLETED, STOPPED
    
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    current_poll_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    question_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", lazy="selectin")
    participants: Mapped[List["GroupQuizParticipant"]] = relationship("GroupQuizParticipant", back_populates="session", cascade="all, delete-orphan", lazy="selectin")
    answers: Mapped[List["GroupQuizAnswer"]] = relationship("GroupQuizAnswer", back_populates="session", cascade="all, delete-orphan", lazy="selectin")


class GroupQuizParticipant(Base):
    __tablename__ = "group_quiz_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    total_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    answers_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GroupQuizSession"] = relationship("GroupQuizSession", back_populates="participants")


class GroupQuizAnswer(Base):
    __tablename__ = "group_quiz_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    selected_option: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_taken_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GroupQuizSession"] = relationship("GroupQuizSession", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", lazy="selectin")
