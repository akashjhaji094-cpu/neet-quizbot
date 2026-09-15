"""Quiz repository."""

import secrets
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models.quiz import Quiz
from app.database.models.question import Question
from app.database.models.attempt import QuizAttempt

class QuizRepository:
    @staticmethod
    def generate_quiz_code() -> str:
        """Generate human-readable unique quiz code, e.g. QUIZ_7F29A."""
        return f"QUIZ_{secrets.token_hex(3).upper()}"

    @classmethod
    def create(
        cls,
        db: Session,
        creator_id: int,
        title: str,
        description: Optional[str] = None
    ) -> Quiz:
        code = cls.generate_quiz_code()
        # Ensure code uniqueness
        while db.query(Quiz).filter(Quiz.quiz_code == code).first():
            code = cls.generate_quiz_code()

        quiz = Quiz(
            creator_id=creator_id,
            quiz_code=code,
            title=title,
            description=description,
            status="DRAFT"
        )
        db.add(quiz)
        db.flush()
        return quiz

    @staticmethod
    def get_by_id(db: Session, quiz_id: int) -> Optional[Quiz]:
        return db.query(Quiz).filter(Quiz.id == quiz_id).first()

    @staticmethod
    def get_by_code(db: Session, quiz_code: str) -> Optional[Quiz]:
        return db.query(Quiz).filter(Quiz.quiz_code == quiz_code).first()

    @staticmethod
    def get_by_creator(db: Session, creator_id: int) -> List[Quiz]:
        return db.query(Quiz).filter(Quiz.creator_id == creator_id).order_by(Quiz.created_at.desc()).all()

    @staticmethod
    def update_description(db: Session, quiz_id: int, description: Optional[str]) -> Optional[Quiz]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            quiz.description = description
            db.flush()
        return quiz

    @staticmethod
    def update_settings(
        db: Session,
        quiz_id: int,
        timer_seconds: Optional[int] = None,
        shuffle_questions: Optional[bool] = None,
        shuffle_options: Optional[bool] = None,
        correct_marks: Optional[float] = None,
        wrong_marks: Optional[float] = None,
        unattempted_marks: Optional[float] = None
    ) -> Optional[Quiz]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            if timer_seconds is not None:
                quiz.timer_seconds = timer_seconds
            if shuffle_questions is not None:
                quiz.shuffle_questions = shuffle_questions
            if shuffle_options is not None:
                quiz.shuffle_options = shuffle_options
            if correct_marks is not None:
                quiz.correct_marks = correct_marks
            if wrong_marks is not None:
                quiz.wrong_marks = wrong_marks
            if unattempted_marks is not None:
                quiz.unattempted_marks = unattempted_marks
            db.flush()
        return quiz

    @staticmethod
    def publish(db: Session, quiz_id: int) -> Optional[Quiz]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            quiz.status = "PUBLISHED"
            db.flush()
        return quiz

    @staticmethod
    def delete(db: Session, quiz_id: int) -> bool:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            db.delete(quiz)
            db.flush()
            return True
        return False

    @staticmethod
    def get_statistics(db: Session, creator_id: int) -> Dict[str, Any]:
        """Aggregate stats for a creator's quizzes."""
        quizzes = db.query(Quiz).filter(Quiz.creator_id == creator_id).all()
        quiz_ids = [q.id for q in quizzes]
        
        if not quiz_ids:
            return {
                "total_quizzes": 0,
                "total_attempts": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "average_percentage": 0.0,
                "total_questions": 0
            }

        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id.in_(quiz_ids),
            QuizAttempt.status == "COMPLETED"
        ).all()

        total_questions = db.query(func.count(Question.id)).filter(
            Question.quiz_id.in_(quiz_ids)
        ).scalar() or 0

        total_attempts = len(attempts)
        if total_attempts == 0:
            return {
                "total_quizzes": len(quizzes),
                "total_attempts": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "average_percentage": 0.0,
                "total_questions": total_questions
            }

        scores = [a.score for a in attempts]
        avg_score = sum(scores) / total_attempts
        highest_score = max(scores)
        lowest_score = min(scores)

        # Average percentage
        percentages = []
        for a in attempts:
            q_count = len(a.quiz.questions) if a.quiz and a.quiz.questions else 1
            max_s = q_count * (a.quiz.correct_marks if a.quiz else 4.0)
            if max_s > 0:
                percentages.append((a.score / max_s) * 100)
        avg_percentage = (sum(percentages) / len(percentages)) if percentages else 0.0

        return {
            "total_quizzes": len(quizzes),
            "total_attempts": total_attempts,
            "average_score": round(avg_score, 2),
            "highest_score": round(highest_score, 2),
            "lowest_score": round(lowest_score, 2),
            "average_percentage": round(avg_percentage, 1),
            "total_questions": total_questions
        }
