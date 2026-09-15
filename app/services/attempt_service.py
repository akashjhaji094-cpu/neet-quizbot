"""Participant quiz attempt execution and answer processing service."""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models.attempt import QuizAttempt, AttemptQuestion, AttemptAnswer
from app.database.models.quiz import Quiz
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.question_repo import QuestionRepository
from app.database.repositories.attempt_repo import AttemptRepository
from app.services.scoring_service import ScoringService


class AttemptService:
    @staticmethod
    def start_attempt(
        db: Session,
        telegram_user_id: int,
        quiz_code: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Tuple[Optional[QuizAttempt], Optional[str]]:
        """Start a new quiz attempt for a participant."""
        user = UserRepository.get_or_create(db, telegram_user_id, username, first_name)
        quiz = QuizRepository.get_by_code(db, quiz_code)
        if not quiz:
            return None, "QUIZ_NOT_FOUND"

        questions = QuestionRepository.get_by_quiz(db, quiz.id)
        if not questions:
            return None, "NO_QUESTIONS"

        # Abandon previous active attempt if any (ensures clean retry)
        active_attempt = AttemptRepository.get_active_attempt(db, user.id)
        if active_attempt:
            AttemptRepository.abandon_attempt(db, active_attempt.id)

        # Question ordering
        question_ids = [q.id for q in questions]
        if quiz.shuffle_questions:
            random.shuffle(question_ids)

        # Option mapping per question
        option_mappings: Dict[int, Dict[str, Any]] = {}
        for q in questions:
            num_options = len(q.options)
            if quiz.shuffle_options and num_options > 1:
                display_to_orig = list(range(num_options))
                random.shuffle(display_to_orig)
                orig_to_display = [display_to_orig.index(i) for i in range(num_options)]
                displayed_correct_index = orig_to_display[q.correct_option_id]
            else:
                display_to_orig = list(range(num_options))
                orig_to_display = list(range(num_options))
                displayed_correct_index = q.correct_option_id

            option_mappings[q.id] = {
                "display_to_orig": display_to_orig,
                "orig_to_display": orig_to_display,
                "displayed_correct_index": displayed_correct_index
            }

        attempt = AttemptRepository.create_attempt(
            db=db,
            quiz_id=quiz.id,
            user_id=user.id,
            ordered_question_ids=question_ids,
            option_mappings=option_mappings
        )
        return attempt, "SUCCESS"

    @staticmethod
    def get_current_question(db: Session, attempt_id: int) -> Optional[Dict[str, Any]]:
        """Get the payload for the question that should currently be delivered."""
        attempt = AttemptRepository.get_by_id(db, attempt_id)
        if not attempt or attempt.status != "IN_PROGRESS":
            return None

        aq = AttemptRepository.get_attempt_question(db, attempt_id, attempt.current_question_index)
        if not aq:
            return None  # Quiz complete

        question = aq.question
        quiz = attempt.quiz
        total_questions = len(attempt.questions)

        # Prepare options in display order
        mapping = aq.option_mapping or {}
        display_to_orig = mapping.get("display_to_orig", list(range(len(question.options))))
        displayed_correct_index = mapping.get("displayed_correct_index", question.correct_option_id)

        orig_options = sorted(question.options, key=lambda o: o.option_index)
        displayed_options = [orig_options[i].option_text for i in display_to_orig]

        # Calculate deadline if timer enabled
        deadline = None
        if quiz.timer_seconds and quiz.timer_seconds > 0:
            deadline = datetime.utcnow() + timedelta(seconds=quiz.timer_seconds)

        return {
            "attempt_question_id": aq.id,
            "attempt_id": attempt.id,
            "question_id": question.id,
            "display_position": aq.display_position + 1,
            "total_questions": total_questions,
            "question_text": question.question_text,
            "options": displayed_options,
            "correct_option_id": displayed_correct_index,
            "explanation": question.explanation,
            "media_file_id": question.media_file_id,
            "media_type": question.media_type,
            "timer_seconds": quiz.timer_seconds,
            "deadline": deadline
        }

    @staticmethod
    def record_poll_sent(
        db: Session,
        attempt_question_id: int,
        poll_id: str,
        message_id: Optional[int] = None,
        deadline: Optional[datetime] = None
    ) -> None:
        AttemptRepository.record_question_delivery(
            db=db,
            attempt_question_id=attempt_question_id,
            poll_id=poll_id,
            message_id=message_id,
            deadline=deadline
        )

    @staticmethod
    def handle_poll_answer(
        db: Session,
        poll_id: str,
        telegram_user_id: int,
        selected_option_index: int
    ) -> Tuple[Optional[AttemptAnswer], bool, Optional[QuizAttempt]]:
        """
        Process a participant's poll answer idempotently.
        Returns (answer, is_quiz_complete, attempt).
        """
        user = UserRepository.get_by_telegram_id(db, telegram_user_id)
        if not user:
            return None, False, None

        aq = AttemptRepository.get_attempt_question_by_poll_id(db, poll_id)
        if not aq:
            return None, False, None

        attempt = aq.attempt
        if not attempt or attempt.user_id != user.id or attempt.status != "IN_PROGRESS":
            return None, False, None

        quiz = attempt.quiz
        mapping = aq.option_mapping or {}
        display_to_orig = mapping.get("display_to_orig", [])

        if selected_option_index < len(display_to_orig):
            orig_selected = display_to_orig[selected_option_index]
        else:
            orig_selected = selected_option_index

        is_correct = (orig_selected == aq.question.correct_option_id)
        marks = ScoringService.evaluate_single_answer(
            is_correct=is_correct,
            is_timeout=False,
            correct_marks=quiz.correct_marks,
            wrong_marks=quiz.wrong_marks,
            unattempted_marks=quiz.unattempted_marks
        )

        answer, is_new = AttemptRepository.record_answer(
            db=db,
            attempt_id=attempt.id,
            question_id=aq.question_id,
            selected_option=orig_selected,
            is_correct=is_correct,
            marks_awarded=marks,
            status="ANSWERED"
        )

        if not is_new:
            return answer, (attempt.status == "COMPLETED"), attempt

        # Check if this was the last question
        is_complete = (attempt.current_question_index >= len(attempt.questions))
        if is_complete:
            AttemptRepository.complete_attempt(db, attempt.id)

        return answer, is_complete, attempt

    @staticmethod
    def handle_timeout(
        db: Session,
        attempt_id: int,
        attempt_question_id: int
    ) -> Tuple[Optional[AttemptAnswer], bool, Optional[QuizAttempt]]:
        """
        Handle server-side question timeout.
        Returns (answer, is_quiz_complete, attempt).
        """
        attempt = AttemptRepository.get_by_id(db, attempt_id)
        if not attempt or attempt.status != "IN_PROGRESS":
            return None, False, None

        aq = db.query(AttemptQuestion).filter(AttemptQuestion.id == attempt_question_id).first()
        if not aq:
            return None, False, None

        quiz = attempt.quiz
        marks = quiz.unattempted_marks

        answer, is_new = AttemptRepository.record_answer(
            db=db,
            attempt_id=attempt.id,
            question_id=aq.question_id,
            selected_option=None,
            is_correct=False,
            marks_awarded=marks,
            status="TIMEOUT"
        )

        if not is_new:
            return answer, (attempt.status == "COMPLETED"), attempt

        is_complete = (attempt.current_question_index >= len(attempt.questions))
        if is_complete:
            AttemptRepository.complete_attempt(db, attempt.id)

        return answer, is_complete, attempt
