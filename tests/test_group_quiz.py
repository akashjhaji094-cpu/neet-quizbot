"""Tests for Group Quiz Session, Multi-User Answer Tracking, and Leaderboard."""

import pytest
from app.services.group_quiz_service import GroupQuizService
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.question_repo import QuestionRepository


def test_group_quiz_multi_user_answers_and_leaderboard(db_session, creator_user):
    """Test group quiz with multiple members, scoring (+4/-1), skipped, and avg time."""
    quiz = QuizRepository.create(db_session, creator_user.id, "Group NEET Biology")
    # Q1: correct is 0
    QuestionRepository.add_question(
        db_session, quiz.id, "Question 1", ["A", "B", "C", "D"], 0
    )
    # Q2: correct is 1
    QuestionRepository.add_question(
        db_session, quiz.id, "Question 2", ["A", "B", "C", "D"], 1
    )
    QuizRepository.update_settings(db_session, quiz.id, timer_seconds=30)
    QuizRepository.publish(db_session, quiz.id)

    chat_id = -1001234567890
    session, status = GroupQuizService.get_or_create_session(db_session, quiz.quiz_code, chat_id)
    assert status == "SUCCESS"
    GroupQuizService.start_session(db_session, session.id)

    # Question 1
    q1_poll = "group_poll_q1"
    GroupQuizService.record_poll_sent(db_session, session.id, q1_poll)

    # User 1 (Akash) answers correctly (option 0)
    GroupQuizService.record_participant_answer(
        db_session, q1_poll, 101, "akash", "Akash", 0
    )
    # User 2 (Rahul) answers wrongly (option 2)
    GroupQuizService.record_participant_answer(
        db_session, q1_poll, 102, "rahul", "Rahul", 2
    )
    # User 3 (Priya) skips Q1 (doesn't answer)

    # Advance to Question 2
    is_fin, _ = GroupQuizService.advance_question_or_finish(db_session, session.id)
    assert is_fin is False

    q2_poll = "group_poll_q2"
    GroupQuizService.record_poll_sent(db_session, session.id, q2_poll)

    # User 1 (Akash) answers Q2 correctly (option 1)
    GroupQuizService.record_participant_answer(
        db_session, q2_poll, 101, "akash", "Akash", 1
    )
    # User 3 (Priya) answers Q2 correctly (option 1)
    GroupQuizService.record_participant_answer(
        db_session, q2_poll, 103, "priya", "Priya", 1
    )
    # User 2 (Rahul) skips Q2

    # Advance and finish
    is_fin2, _ = GroupQuizService.advance_question_or_finish(db_session, session.id)
    assert is_fin2 is True

    # Check Leaderboard
    leaderboard = GroupQuizService.generate_leaderboard_data(db_session, session.id)
    rankings = leaderboard["rankings"]
    assert len(rankings) == 3

    # Rank 1: Akash (2 correct, 0 wrong, 0 skipped = 8 pts)
    assert rankings[0]["name"] == "@akash"
    assert rankings[0]["score"] == 8
    assert rankings[0]["correct"] == 2
    assert rankings[0]["wrong"] == 0
    assert rankings[0]["skipped"] == 0

    # Rank 2: Priya (1 correct, 0 wrong, 1 skipped = 4 pts)
    assert rankings[1]["name"] == "@priya"
    assert rankings[1]["score"] == 4
    assert rankings[1]["correct"] == 1
    assert rankings[1]["wrong"] == 0
    assert rankings[1]["skipped"] == 1

    # Rank 3: Rahul (0 correct, 1 wrong, 1 skipped = -1 pt)
    assert rankings[2]["name"] == "@rahul"
    assert rankings[2]["score"] == -1
    assert rankings[2]["correct"] == 0
    assert rankings[2]["wrong"] == 1
    assert rankings[2]["skipped"] == 1
