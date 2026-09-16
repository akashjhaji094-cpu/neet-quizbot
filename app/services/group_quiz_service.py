"""Group Quiz Session, Answer Tracking, and Leaderboard Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models.quiz import Quiz
from app.database.models.group_quiz import GroupQuizSession, GroupQuizParticipant, GroupQuizAnswer
from app.database.repositories.quiz_repo import QuizRepository
from app.utils.logger import logger


class GroupQuizService:
    @staticmethod
    def get_or_create_session(
        db: Session,
        quiz_code: str,
        chat_id: int
    ) -> Tuple[Optional[GroupQuizSession], Optional[str]]:
        """Find or initialize a group quiz session."""
        quiz = QuizRepository.get_by_code(db, quiz_code)
        if not quiz:
            return None, "QUIZ_NOT_FOUND"

        if not quiz.questions:
            return None, "NO_QUESTIONS"

        # Check for existing waiting/in-progress session in this group
        session = (
            db.query(GroupQuizSession)
            .filter(
                GroupQuizSession.chat_id == chat_id,
                GroupQuizSession.status.in_(["WAITING", "IN_PROGRESS"])
            )
            .order_by(GroupQuizSession.started_at.desc())
            .first()
        )

        if session:
            # If quiz is different or finished, stop old session
            if session.quiz_id != quiz.id:
                session.status = "STOPPED"
                db.flush()
                session = None

        if not session:
            session = GroupQuizSession(
                quiz_id=quiz.id,
                chat_id=chat_id,
                status="WAITING",
                current_question_index=0
            )
            db.add(session)
            db.flush()

        return session, "SUCCESS"

    @staticmethod
    def start_session(db: Session, session_id: int) -> Optional[GroupQuizSession]:
        """Start the quiz session in the group."""
        session = db.query(GroupQuizSession).filter(GroupQuizSession.id == session_id).first()
        if session:
            session.status = "IN_PROGRESS"
            session.current_question_index = 0
            session.started_at = datetime.utcnow()
            db.flush()
        return session

    @staticmethod
    def get_current_question_payload(db: Session, session_id: int) -> Optional[Dict[str, Any]]:
        """Get question data to be delivered to the group."""
        session = db.query(GroupQuizSession).filter(GroupQuizSession.id == session_id).first()
        if not session or session.status != "IN_PROGRESS":
            return None

        quiz = session.quiz
        questions = quiz.questions
        if session.current_question_index >= len(questions):
            return None  # All questions finished

        q = questions[session.current_question_index]
        orig_options = sorted(q.options, key=lambda o: o.option_index)
        options_text = [opt.option_text for opt in orig_options]

        return {
            "session_id": session.id,
            "quiz_title": quiz.title,
            "question_id": q.id,
            "display_position": session.current_question_index + 1,
            "total_questions": len(questions),
            "question_text": q.question_text,
            "options": options_text,
            "correct_option_id": q.correct_option_id,
            "explanation": q.explanation,
            "media_file_id": q.media_file_id,
            "media_type": q.media_type,
            "timer_seconds": quiz.timer_seconds if (quiz.timer_seconds and quiz.timer_seconds > 0) else 30
        }

    @staticmethod
    def record_poll_sent(db: Session, session_id: int, poll_id: str) -> None:
        """Record the poll ID and timestamp for group response time calculation."""
        session = db.query(GroupQuizSession).filter(GroupQuizSession.id == session_id).first()
        if session:
            session.current_poll_id = poll_id
            session.question_sent_at = datetime.utcnow()
            db.flush()

    @staticmethod
    def record_participant_answer(
        db: Session,
        poll_id: str,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        selected_option: int
    ) -> bool:
        """
        Record a group member's poll answer, tracking time taken and NEET scoring (+4/-1).
        Idempotent: One answer per participant per question.
        """
        session = (
            db.query(GroupQuizSession)
            .filter(
                GroupQuizSession.current_poll_id == poll_id,
                GroupQuizSession.status == "IN_PROGRESS"
            )
            .first()
        )
        if not session:
            return False

        quiz = session.quiz
        if session.current_question_index >= len(quiz.questions):
            return False

        current_question = quiz.questions[session.current_question_index]

        # Check if user already answered this question in this session
        existing_answer = (
            db.query(GroupQuizAnswer)
            .filter(
                GroupQuizAnswer.session_id == session.id,
                GroupQuizAnswer.question_id == current_question.id,
                GroupQuizAnswer.telegram_user_id == user_id
            )
            .first()
        )
        if existing_answer:
            return False

        # Calculate time taken
        sent_at = session.question_sent_at or datetime.utcnow()
        time_taken = max(0.1, round((datetime.utcnow() - sent_at).total_seconds(), 2))

        is_correct = (selected_option == current_question.correct_option_id)

        # Record individual answer
        answer = GroupQuizAnswer(
            session_id=session.id,
            question_id=current_question.id,
            telegram_user_id=user_id,
            selected_option=selected_option,
            is_correct=is_correct,
            time_taken_seconds=time_taken,
            answered_at=datetime.utcnow()
        )
        db.add(answer)

        # Find or create participant record in this session
        participant = (
            db.query(GroupQuizParticipant)
            .filter(
                GroupQuizParticipant.session_id == session.id,
                GroupQuizParticipant.telegram_user_id == user_id
            )
            .first()
        )
        if not participant:
            participant = GroupQuizParticipant(
                session_id=session.id,
                telegram_user_id=user_id,
                username=username,
                first_name=first_name,
                correct_count=0,
                wrong_count=0,
                skipped_count=0,
                total_time_seconds=0.0,
                answers_count=0,
                score=0.0
            )
            db.add(participant)
            db.flush()
        else:
            # Update name if changed
            if username:
                participant.username = username
            if first_name:
                participant.first_name = first_name

        # Update participant statistics
        participant.answers_count += 1
        participant.total_time_seconds += time_taken

        if is_correct:
            participant.correct_count += 1
            participant.score += quiz.correct_marks
        else:
            participant.wrong_count += 1
            participant.score += quiz.wrong_marks

        db.flush()
        return True

    @staticmethod
    def advance_question_or_finish(db: Session, session_id: int) -> Tuple[bool, Optional[GroupQuizSession]]:
        """
        Advance to the next question or mark session COMPLETED.
        Returns (is_finished, session).
        """
        session = db.query(GroupQuizSession).filter(GroupQuizSession.id == session_id).first()
        if not session or session.status != "IN_PROGRESS":
            return True, None

        session.current_question_index += 1
        total_questions = len(session.quiz.questions)

        if session.current_question_index >= total_questions:
            session.status = "COMPLETED"
            session.completed_at = datetime.utcnow()

            participants = db.query(GroupQuizParticipant).filter(GroupQuizParticipant.session_id == session.id).all()
            for p in participants:
                p.skipped_count = max(0, total_questions - p.answers_count)

            db.flush()
            return True, session
        else:
            db.flush()
            return False, session

    @staticmethod
    def generate_leaderboard_data(db: Session, session_id: int) -> Dict[str, Any]:
        """Generate ranked leaderboard data with scores, correct, wrong, skipped, and avg time."""
        session = db.query(GroupQuizSession).filter(GroupQuizSession.id == session_id).first()
        if not session:
            return {"quiz_title": "Quiz", "total_questions": 0, "rankings": []}

        quiz = session.quiz
        total_q = len(quiz.questions)
        participants = db.query(GroupQuizParticipant).filter(GroupQuizParticipant.session_id == session.id).all()

        # Compute skipped and avg time
        rankings = []
        for p in participants:
            skipped = max(0, total_q - p.answers_count)
            avg_time = round(p.total_time_seconds / p.answers_count, 1) if p.answers_count > 0 else 0.0

            name = f"@{p.username}" if p.username else (p.first_name or f"User_{p.telegram_user_id}")

            rankings.append({
                "user_id": p.telegram_user_id,
                "name": name,
                "score": int(p.score) if p.score.is_integer() else p.score,
                "correct": p.correct_count,
                "wrong": p.wrong_count,
                "skipped": skipped,
                "avg_time": avg_time,
                "sort_key": (-p.score, avg_time)
            })

        # Rank by highest score, tie-break by lowest average time
        rankings.sort(key=lambda x: x["sort_key"])

        # Add rank medals
        medals = ["🥇", "🥈", "🥉"]
        for idx, item in enumerate(rankings):
            rank_num = idx + 1
            item["medal"] = medals[idx] if idx < 3 else f"{rank_num}."

        return {
            "quiz_title": quiz.title,
            "total_questions": total_q,
            "rankings": rankings,
            "total_participants": len(rankings)
        }
