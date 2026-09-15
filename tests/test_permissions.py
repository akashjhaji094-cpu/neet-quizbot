"""Tests for Creator and Participant Permissions."""

import pytest
from app.services.quiz_service import QuizService
from app.services.attempt_service import AttemptService
from app.database.repositories.quiz_repo import QuizRepository


def test_participant_cannot_undo_or_cancel_creator_quiz(db_session, sample_quiz, participant_user):
    """Participant cannot undo or cancel another user's quiz draft."""
    # Participant tries to undo
    removed, count = QuizService.undo_last_question(db_session, participant_user.telegram_user_id)
    assert removed is None
    assert count == 0

    # Participant tries to cancel
    cancelled = QuizService.cancel_draft(db_session, participant_user.telegram_user_id)
    assert cancelled is False

    # Sample quiz remains published and intact
    q = QuizRepository.get_by_id(db_session, sample_quiz.id)
    assert q is not None
    assert q.status == "PUBLISHED"


def test_unauthorized_user_poll_answer_ignored(db_session, sample_quiz, participant_user):
    """Poll answer from a user not owning the attempt is rejected."""
    attempt, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, sample_quiz.quiz_code
    )
    q1 = AttemptService.get_current_question(db_session, attempt.id)
    poll_id = "perm_poll_test"
    AttemptService.record_poll_sent(db_session, q1["attempt_question_id"], poll_id)

    # Some random user sends poll_answer
    random_user_id = 999999999
    ans, is_comp, att = AttemptService.handle_poll_answer(
        db_session, poll_id, random_user_id, q1["correct_option_id"]
    )
    assert ans is None
    assert att is None
    assert is_comp is False
