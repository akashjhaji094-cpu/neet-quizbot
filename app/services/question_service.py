"""Question creation and pre-question media handling service."""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models.question import Question
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.draft_repo import DraftRepository
from app.database.repositories.question_repo import QuestionRepository


class QuestionService:
    @staticmethod
    def set_pending_media(
        db: Session,
        telegram_user_id: int,
        media_file_id: str,
        media_type: str
    ) -> bool:
        """Store media to be attached to the upcoming question."""
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return False
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return False
        DraftRepository.set_pending_media(db, user.id, media_file_id, media_type)
        return True

    @staticmethod
    def add_native_poll_question(
        db: Session,
        telegram_user_id: int,
        question_text: str,
        options: List[str],
        correct_option_id: int,
        explanation: Optional[str] = None,
        telegram_poll_id: Optional[str] = None,
        telegram_message_id: Optional[int] = None
    ) -> Tuple[Optional[Question], int]:
        """Save a question received from Telegram native poll creation."""
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None, 0
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None, 0

        # Retrieve and consume any pending pre-question media
        media_file_id = draft.pending_media_file_id
        media_type = draft.pending_media_type

        question = QuestionRepository.add_question(
            db=db,
            quiz_id=draft.quiz_id,
            question_text=question_text,
            options=options,
            correct_option_id=correct_option_id,
            explanation=explanation,
            media_file_id=media_file_id,
            media_type=media_type,
            telegram_poll_id=telegram_poll_id,
            telegram_message_id=telegram_message_id
        )

        # Clear pending media once consumed
        DraftRepository.clear_pending_media(db, user.id)

        count = QuestionRepository.count_by_quiz(db, draft.quiz_id)
        return question, count
