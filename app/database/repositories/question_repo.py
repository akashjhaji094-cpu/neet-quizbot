"""Question and Option repository."""

from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models.question import Question
from app.database.models.option import Option

class QuestionRepository:
    @staticmethod
    def add_question(
        db: Session,
        quiz_id: int,
        question_text: str,
        options: List[str],
        correct_option_id: int,
        explanation: Optional[str] = None,
        media_file_id: Optional[str] = None,
        media_type: Optional[str] = None,
        telegram_poll_id: Optional[str] = None,
        telegram_message_id: Optional[int] = None
    ) -> Question:
        current_max = db.query(func.max(Question.position)).filter(Question.quiz_id == quiz_id).scalar() or 0
        new_pos = current_max + 1

        question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            correct_option_id=correct_option_id,
            explanation=explanation,
            media_file_id=media_file_id,
            media_type=media_type,
            telegram_poll_id=telegram_poll_id,
            telegram_message_id=telegram_message_id,
            position=new_pos
        )
        db.add(question)
        db.flush()

        for idx, opt_text in enumerate(options):
            opt = Option(
                question_id=question.id,
                option_index=idx,
                option_text=opt_text
            )
            db.add(opt)
        
        db.flush()
        return question

    @staticmethod
    def get_by_id(db: Session, question_id: int) -> Optional[Question]:
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def get_by_quiz(db: Session, quiz_id: int) -> List[Question]:
        return db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.position.asc()).all()

    @staticmethod
    def count_by_quiz(db: Session, quiz_id: int) -> int:
        return db.query(func.count(Question.id)).filter(Question.quiz_id == quiz_id).scalar() or 0

    @staticmethod
    def remove_latest(db: Session, quiz_id: int) -> Optional[Question]:
        latest_question = (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.position.desc())
            .first()
        )
        if latest_question:
            db.delete(latest_question)
            db.flush()
            return latest_question
        return None

    @staticmethod
    def get_by_poll_id(db: Session, poll_id: str) -> Optional[Question]:
        return db.query(Question).filter(Question.telegram_poll_id == poll_id).first()
