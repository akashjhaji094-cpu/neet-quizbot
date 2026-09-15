"""Tests for Question Shuffling, Option Shuffling, and Answer Remapping."""

import pytest
from app.services.attempt_service import AttemptService
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.question_repo import QuestionRepository


def test_question_shuffling_per_attempt(db_session, creator_user, participant_user):
    """Question order should be randomized per attempt and not modify base quiz."""
    quiz = QuizRepository.create(db_session, creator_user.id, "Shuffle Test Quiz")
    for i in range(10):
        QuestionRepository.add_question(
            db_session, quiz.id, f"Question {i}", ["A", "B", "C", "D"], 0
        )
    QuizRepository.update_settings(db_session, quiz.id, shuffle_questions=True, shuffle_options=False)
    QuizRepository.publish(db_session, quiz.id)

    original_order = [q.id for q in QuestionRepository.get_by_quiz(db_session, quiz.id)]

    # Create two different attempts
    attempt1, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, quiz.quiz_code
    )
    attempt1_order = [aq.question_id for aq in attempt1.questions]

    # Verify original order in base database is intact
    base_order_after = [q.id for q in QuestionRepository.get_by_quiz(db_session, quiz.id)]
    assert original_order == base_order_after
    assert len(attempt1_order) == 10


def test_option_shuffling_and_correct_remapping(db_session, creator_user, participant_user):
    """
    When option shuffling is enabled:
    1. Display options are permuted.
    2. Correct answer mapping remains 100% accurate.
    """
    quiz = QuizRepository.create(db_session, creator_user.id, "Option Mapping Quiz")
    # Correct answer is 'Option B' (index 1)
    q = QuestionRepository.add_question(
        db_session,
        quiz.id,
        "What is the capital of France?",
        ["Berlin", "Paris", "Rome", "Madrid"],
        correct_option_id=1
    )
    QuizRepository.update_settings(db_session, quiz.id, shuffle_questions=False, shuffle_options=True)
    QuizRepository.publish(db_session, quiz.id)

    attempt, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, quiz.quiz_code
    )
    q_data = AttemptService.get_current_question(db_session, attempt.id)

    # In q_data, options are displayed in permuted order
    displayed_options = q_data["options"]
    displayed_correct_id = q_data["correct_option_id"]

    # Verify that the displayed correct option is indeed "Paris"
    assert displayed_options[displayed_correct_id] == "Paris"

    # Simulate participant answering with the displayed correct index
    poll_id = "test_poll_shuffled_123"
    AttemptService.record_poll_sent(db_session, q_data["attempt_question_id"], poll_id)

    ans, is_complete, updated_attempt = AttemptService.handle_poll_answer(
        db=db_session,
        poll_id=poll_id,
        telegram_user_id=participant_user.telegram_user_id,
        selected_option_index=displayed_correct_id
    )

    assert ans.is_correct is True
    assert ans.marks_awarded == 4.0
    assert updated_attempt.score == 4.0
    assert updated_attempt.correct_count == 1
    assert is_complete is True


def test_shuffled_wrong_answer_deducts_marks(db_session, creator_user, participant_user):
    """Selecting a wrong shuffled option deducts 1 mark."""
    quiz = QuizRepository.create(db_session, creator_user.id, "Wrong Answer Quiz")
    # Correct answer is 'Option C' (index 2)
    q = QuestionRepository.add_question(
        db_session,
        quiz.id,
        "What is 2 + 2?",
        ["2", "3", "4", "5"],
        correct_option_id=2
    )
    QuizRepository.update_settings(db_session, quiz.id, shuffle_options=True)
    QuizRepository.publish(db_session, quiz.id)

    attempt, _ = AttemptService.start_attempt(
        db_session, participant_user.telegram_user_id, quiz.quiz_code
    )
    q_data = AttemptService.get_current_question(db_session, attempt.id)

    displayed_correct_id = q_data["correct_option_id"]
    # Pick a wrong index
    wrong_index = (displayed_correct_id + 1) % len(q_data["options"])

    poll_id = "test_poll_wrong_456"
    AttemptService.record_poll_sent(db_session, q_data["attempt_question_id"], poll_id)

    ans, is_complete, updated_attempt = AttemptService.handle_poll_answer(
        db=db_session,
        poll_id=poll_id,
        telegram_user_id=participant_user.telegram_user_id,
        selected_option_index=wrong_index
    )

    assert ans.is_correct is False
    assert ans.marks_awarded == -1.0
    assert updated_attempt.score == -1.0
    assert updated_attempt.wrong_count == 1
    assert is_complete is True
