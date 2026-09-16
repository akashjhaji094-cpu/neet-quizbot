"""Quiz creation and management service."""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models.quiz import Quiz
from app.database.models.question import Question
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.question_repo import QuestionRepository
from app.database.repositories.draft_repo import DraftRepository


class QuizService:
    @staticmethod
    def start_new_quiz(
        db: Session,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Tuple[Optional[Quiz], str]:
        """Start a new quiz creation session."""
        user = UserRepository.get_or_create(db, telegram_user_id, username, first_name)
        active_draft = DraftRepository.get_by_user_id(db, user.id)

        if active_draft:
            # Check if quiz still exists
            quiz = QuizRepository.get_by_id(db, active_draft.quiz_id)
            if quiz and quiz.status == "DRAFT":
                return quiz, "UNFINISHED_EXISTS"
            else:
                DraftRepository.delete_by_user_id(db, user.id)

        # Create new draft quiz
        quiz = QuizRepository.create(
            db=db,
            creator_id=user.id,
            title="Untitled Quiz",
            description=None
        )
        DraftRepository.create_or_update(
            db=db,
            user_id=user.id,
            quiz_id=quiz.id,
            state="WAITING_TITLE"
        )
        return quiz, "SUCCESS"

    @staticmethod
    def get_active_draft_state(db: Session, telegram_user_id: int) -> Tuple[Optional[Quiz], Optional[str]]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None, None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None, None
        quiz = QuizRepository.get_by_id(db, draft.quiz_id)
        if not quiz or quiz.status != "DRAFT":
            DraftRepository.delete_by_user_id(db, user.id)
            return None, None
        return quiz, draft.state

    @staticmethod
    def set_title(db: Session, telegram_user_id: int, title: str) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz = QuizRepository.get_by_id(db, draft.quiz_id)
        if quiz:
            quiz.title = title.strip()
            draft.state = "WAITING_DESCRIPTION"
            db.flush()
        return quiz

    @staticmethod
    def set_description(db: Session, telegram_user_id: int, description: Optional[str]) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz = QuizRepository.get_by_id(db, draft.quiz_id)
        if quiz:
            quiz.description = description.strip() if description else None
            draft.state = "WAITING_QUESTIONS"
            db.flush()
        return quiz

    @staticmethod
    def undo_last_question(db: Session, telegram_user_id: int) -> Tuple[Optional[Question], int]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None, 0
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None, 0
        removed = QuestionRepository.remove_latest(db, draft.quiz_id)
        remaining_count = QuestionRepository.count_by_quiz(db, draft.quiz_id)
        return removed, remaining_count

    @staticmethod
    def cancel_draft(db: Session, telegram_user_id: int) -> bool:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return False
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return False
        quiz_id = draft.quiz_id
        DraftRepository.delete_by_user_id(db, user.id)
        quiz = QuizRepository.get_by_id(db, quiz_id)
        if quiz and quiz.status == "DRAFT":
            QuizRepository.delete(db, quiz_id)
        return True

    @staticmethod
    def finish_questions(db: Session, telegram_user_id: int) -> Tuple[bool, int]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return False, 0
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return False, 0
        count = QuestionRepository.count_by_quiz(db, draft.quiz_id)
        if count == 0:
            return False, 0
        draft.state = "WAITING_TIMER"
        db.flush()
        return True, count

    @staticmethod
    def set_timer(db: Session, telegram_user_id: int, timer_seconds: int) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz = QuizRepository.update_settings(db, draft.quiz_id, timer_seconds=timer_seconds)
        draft.state = "WAITING_SHUFFLE"
        db.flush()
        return quiz

    @staticmethod
    def set_shuffle(
        db: Session,
        telegram_user_id: int,
        shuffle_questions: bool,
        shuffle_options: bool
    ) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz = QuizRepository.update_settings(
            db,
            draft.quiz_id,
            shuffle_questions=shuffle_questions,
            shuffle_options=shuffle_options
        )
        return quiz

    @staticmethod
    def set_marking(
        db: Session,
        telegram_user_id: int,
        correct_marks: float,
        wrong_marks: float,
        unattempted_marks: float = 0.0
    ) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz = QuizRepository.update_settings(
            db,
            draft.quiz_id,
            correct_marks=correct_marks,
            wrong_marks=wrong_marks,
            unattempted_marks=unattempted_marks
        )
        return quiz

    @staticmethod
    def publish_draft(db: Session, telegram_user_id: int) -> Optional[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None
        draft = DraftRepository.get_by_user_id(db, user.id)
        if not draft:
            return None
        quiz_id = draft.quiz_id
        quiz = QuizRepository.publish(db, quiz_id)
        DraftRepository.delete_by_user_id(db, user.id)
        return quiz

    @staticmethod
    def get_user_quizzes(db: Session, telegram_user_id: int) -> List[Quiz]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return []
        return QuizRepository.get_by_creator(db, user.id)

    @staticmethod
    def get_creator_stats(db: Session, telegram_user_id: int) -> Dict[str, Any]:
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return {
                "total_quizzes": 0,
                "total_attempts": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "average_percentage": 0.0,
                "total_questions": 0
            }
        return QuizRepository.get_statistics(db, user.id)

    @staticmethod
    def generate_deep_link(bot_username: str, quiz_code: str) -> str:
        clean_bot = bot_username.lstrip("@")
        return f"https://t.me/{clean_bot}?start=quiz_{quiz_code}"
