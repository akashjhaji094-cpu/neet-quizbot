"""Quiz Attempt and Answer repository."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models.attempt import QuizAttempt, AttemptQuestion, AttemptAnswer

class AttemptRepository:
    @staticmethod
    def create_attempt(
        db: Session,
        quiz_id: int,
        user_id: int,
        ordered_question_ids: List[int],
        option_mappings: Dict[int, Dict[str, Any]]
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            status="IN_PROGRESS",
            current_question_index=0,
            score=0.0,
            correct_count=0,
            wrong_count=0,
            unattempted_count=0,
            started_at=datetime.utcnow()
        )
        db.add(attempt)
        db.flush()

        for pos, qid in enumerate(ordered_question_ids):
            mapping = option_mappings.get(qid)
            aq = AttemptQuestion(
                attempt_id=attempt.id,
                question_id=qid,
                display_position=pos,
                option_mapping=mapping
            )
            db.add(aq)

        db.flush()
        return attempt

    @staticmethod
    def get_by_id(db: Session, attempt_id: int) -> Optional[QuizAttempt]:
        return db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()

    @staticmethod
    def get_active_attempt(db: Session, user_id: int) -> Optional[QuizAttempt]:
        return (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.status == "IN_PROGRESS"
            )
            .order_by(QuizAttempt.started_at.desc())
            .first()
        )

    @staticmethod
    def get_attempt_question(db: Session, attempt_id: int, display_position: int) -> Optional[AttemptQuestion]:
        return (
            db.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == attempt_id,
                AttemptQuestion.display_position == display_position
            )
            .first()
        )

    @staticmethod
    def get_attempt_question_by_poll_id(db: Session, poll_id: str) -> Optional[AttemptQuestion]:
        return (
            db.query(AttemptQuestion)
            .filter(AttemptQuestion.telegram_poll_id == poll_id)
            .first()
        )

    @staticmethod
    def record_question_delivery(
        db: Session,
        attempt_question_id: int,
        poll_id: str,
        message_id: Optional[int] = None,
        deadline: Optional[datetime] = None
    ) -> None:
        aq = db.query(AttemptQuestion).filter(AttemptQuestion.id == attempt_question_id).first()
        if aq:
            aq.telegram_poll_id = poll_id
            aq.telegram_message_id = message_id
            aq.sent_at = datetime.utcnow()
            aq.deadline = deadline
            db.flush()

    @staticmethod
    def record_answer(
        db: Session,
        attempt_id: int,
        question_id: int,
        selected_option: Optional[int],
        is_correct: bool,
        marks_awarded: float,
        status: str = "ANSWERED"
    ) -> Tuple[AttemptAnswer, bool]:
        """Record an answer idempotently. Returns (answer, is_new_answer)."""
        existing = (
            db.query(AttemptAnswer)
            .filter(
                AttemptAnswer.attempt_id == attempt_id,
                AttemptAnswer.question_id == question_id
            )
            .first()
        )
        if existing:
            return existing, False

        answer = AttemptAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option=selected_option,
            is_correct=is_correct,
            marks_awarded=marks_awarded,
            answered_at=datetime.utcnow(),
            status=status
        )
        db.add(answer)

        # Update attempt stats
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if attempt:
            attempt.score += marks_awarded
            if status == "TIMEOUT" or status == "UNATTEMPTED":
                attempt.unattempted_count += 1
            elif is_correct:
                attempt.correct_count += 1
            else:
                attempt.wrong_count += 1
            attempt.current_question_index += 1

        db.flush()
        return answer, True

    @staticmethod
    def complete_attempt(db: Session, attempt_id: int) -> Optional[QuizAttempt]:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if attempt:
            attempt.status = "COMPLETED"
            attempt.completed_at = datetime.utcnow()
            db.flush()
        return attempt

    @staticmethod
    def abandon_attempt(db: Session, attempt_id: int) -> Optional[QuizAttempt]:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if attempt:
            attempt.status = "ABANDONED"
            attempt.completed_at = datetime.utcnow()
            db.flush()
        return attempt
