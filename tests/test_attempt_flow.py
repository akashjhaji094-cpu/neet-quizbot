"""Tests for Participant Attempt lifecycle, timeouts, idempotency, retries, and stats."""

import pytest
from app.database.models.attempt import QuizAttempt
from app.services.attempt_service import AttemptService
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.attempt_repo import AttemptRepository


def test_full_attempt_execution(db_session, sample_quiz, participant_user):
    """Participant answers all questions and finishes quiz."""
    attempt, status = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    assert status == "SUCCESS"
    assert attempt.status == "IN_PROGRESS"

    # Question 1
    q1 = AttemptService.get_current_question(db_session, attempt.id)
    assert q1 is not None
    poll_id_1 = "poll_q1"
    AttemptService.record_poll_sent(db_session, q1["attempt_question_id"], poll_id_1)

    # Answer Q1 correctly
    ans1, is_comp1, att1 = AttemptService.handle_poll_answer(
        db_session, poll_id_1, participant_user.telegram_user_id, q1["correct_option_id"]
    )
    assert is_comp1 is False
    assert att1.score == 4.0

    # Question 2
    q2 = AttemptService.get_current_question(db_session, attempt.id)
    assert q2 is not None
    poll_id_2 = "poll_q2"
    AttemptService.record_poll_sent(db_session, q2["attempt_question_id"], poll_id_2)

    # Answer Q2 incorrectly
    wrong_opt = (q2["correct_option_id"] + 1) % len(q2["options"])
    ans2, is_comp2, att2 = AttemptService.handle_poll_answer(
        db_session, poll_id_2, participant_user.telegram_user_id, wrong_opt
    )
    assert is_comp2 is True
    assert att2.status == "COMPLETED"
    assert att2.correct_count == 1
    assert att2.wrong_count == 1
    assert att2.score == 3.0  # +4 - 1 = 3


def test_question_timeout_awards_zero_marks(db_session, sample_quiz, participant_user):
    """When a timer expires, question is recorded as TIMEOUT with 0 marks."""
    attempt, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    q1 = AttemptService.get_current_question(db_session, attempt.id)

    # Trigger server-side timeout
    ans, is_comp, att = AttemptService.handle_timeout(
        db_session, attempt.id, q1["attempt_question_id"]
    )
    assert ans.status == "TIMEOUT"
    assert ans.marks_awarded == 0.0
    assert ans.is_correct is False
    assert att.unattempted_count == 1
    assert att.score == 0.0
    assert is_comp is False


def test_idempotency_duplicate_poll_answers(db_session, sample_quiz, participant_user):
    """Duplicate Telegram poll_answer updates must not award double marks."""
    attempt, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    q1 = AttemptService.get_current_question(db_session, attempt.id)
    poll_id = "poll_id_dup_test"
    AttemptService.record_poll_sent(db_session, q1["attempt_question_id"], poll_id)

    # First answer delivery
    ans1, _, att1 = AttemptService.handle_poll_answer(
        db_session, poll_id, participant_user.telegram_user_id, q1["correct_option_id"]
    )
    score_after_first = att1.score

    # Duplicate delivery of same answer
    ans2, _, att2 = AttemptService.handle_poll_answer(
        db_session, poll_id, participant_user.telegram_user_id, q1["correct_option_id"]
    )
    assert att2.score == score_after_first
    assert att2.correct_count == 1


def test_retry_creates_new_attempt_and_preserves_history(db_session, sample_quiz, participant_user):
    """Retry ('Try Again') creates a brand new attempt without deleting previous results."""
    # Attempt 1
    att1, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    AttemptRepository.complete_attempt(db_session, att1.id)

    # Attempt 2 (Retry)
    att2, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    assert att2.id != att1.id

    # Verify both attempts exist in database
    all_user_attempts = (
        db_session.query(QuizAttempt)
        .filter(QuizAttempt.user_id == participant_user.id)
        .all()
    )
    assert len(all_user_attempts) == 2


def test_creator_statistics_calculation(db_session, sample_quiz, participant_user, creator_user):
    """Test statistics aggregation for creator."""
    # Complete an attempt with score 4.0
    att, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    att.score = 4.0
    att.status = "COMPLETED"
    db_session.flush()

    stats = QuizRepository.get_statistics(db_session, creator_user.id)
    assert stats["total_quizzes"] == 1
    assert stats["total_attempts"] == 1
    assert stats["average_score"] == 4.0
    assert stats["highest_score"] == 4.0
    assert stats["total_questions"] == 2
