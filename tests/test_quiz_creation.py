"""Tests for Quiz Creation flow, draft persistence, and commands."""

import pytest
from app.services.quiz_service import QuizService
from app.services.question_service import QuestionService
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.draft_repo import DraftRepository
from app.database.repositories.quiz_repo import QuizRepository


def test_start_new_quiz_flow(db_session, creator_user):
    """Creator can initiate a new quiz and draft session is created."""
    quiz, status = QuizService.start_new_quiz(
        db=db_session,
        telegram_user_id=creator_user.telegram_user_id,
        username=creator_user.username
    )
    assert status == "SUCCESS"
    assert quiz is not None
    assert quiz.status == "DRAFT"

    # Verify draft state
    draft = DraftRepository.get_by_user_id(db_session, creator_user.id)
    assert draft is not None
    assert draft.state == "WAITING_TITLE"


def test_cannot_start_second_quiz_if_unfinished(db_session, creator_user):
    """User cannot create a second quiz if an active draft exists."""
    quiz1, status1 = QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    assert status1 == "SUCCESS"

    quiz2, status2 = QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    assert status2 == "UNFINISHED_EXISTS"
    assert quiz2.id == quiz1.id


def test_quiz_title_and_description_flow(db_session, creator_user):
    """Test setting title and description."""
    quiz, _ = QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    
    # Set title
    updated_quiz = QuizService.set_title(db_session, creator_user.telegram_user_id, "Physics - Mechanics")
    assert updated_quiz.title == "Physics - Mechanics"
    _, state = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state == "WAITING_DESCRIPTION"

    # Set description
    updated_quiz = QuizService.set_description(db_session, creator_user.telegram_user_id, "Laws of motion questions")
    assert updated_quiz.description == "Laws of motion questions"
    _, state = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state == "WAITING_QUESTIONS"


def test_prequestion_media_attachment(db_session, creator_user):
    """Pre-question media sent before poll is attached to the upcoming question."""
    QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    QuizService.set_title(db_session, creator_user.telegram_user_id, "Chemistry Test")
    QuizService.set_description(db_session, creator_user.telegram_user_id, None)

    # Attach photo media
    QuestionService.set_pending_media(
        db=db_session,
        telegram_user_id=creator_user.telegram_user_id,
        media_file_id="photo_file_id_abc123",
        media_type="photo"
    )

    # Now add question via native poll
    q, count = QuestionService.add_native_poll_question(
        db=db_session,
        telegram_user_id=creator_user.telegram_user_id,
        question_text="Identify the molecular geometry shown in the image.",
        options=["Linear", "Trigonal Planar", "Tetrahedral", "Bent"],
        correct_option_id=2
    )

    assert count == 1
    assert q.media_file_id == "photo_file_id_abc123"
    assert q.media_type == "photo"

    # Pending media must be cleared for subsequent question
    draft = DraftRepository.get_by_user_id(db_session, creator_user.id)
    assert draft.pending_media_file_id is None


def test_undo_removes_latest_question(db_session, creator_user):
    """/undo removes the most recently added question."""
    QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    QuizService.set_title(db_session, creator_user.telegram_user_id, "Botany Test")
    QuizService.set_description(db_session, creator_user.telegram_user_id, None)

    # Add question 1
    QuestionService.add_native_poll_question(
        db_session, creator_user.telegram_user_id,
        "Q1 Text", ["A", "B"], 0
    )
    # Add question 2
    QuestionService.add_native_poll_question(
        db_session, creator_user.telegram_user_id,
        "Q2 Text", ["C", "D"], 1
    )

    # Undo question 2
    removed, count = QuizService.undo_last_question(db_session, creator_user.telegram_user_id)
    assert removed.question_text == "Q2 Text"
    assert count == 1

    # Undo question 1
    removed2, count2 = QuizService.undo_last_question(db_session, creator_user.telegram_user_id)
    assert removed2.question_text == "Q1 Text"
    assert count2 == 0

    # Undo when empty
    removed3, count3 = QuizService.undo_last_question(db_session, creator_user.telegram_user_id)
    assert removed3 is None
    assert count3 == 0


def test_finish_questions_validation(db_session, creator_user):
    """/done requires at least one question."""
    QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    QuizService.set_title(db_session, creator_user.telegram_user_id, "Test")
    QuizService.set_description(db_session, creator_user.telegram_user_id, None)

    # 0 questions: /done must fail
    success, _ = QuizService.finish_questions(db_session, creator_user.telegram_user_id)
    assert success is False

    # Add question
    QuestionService.add_native_poll_question(
        db_session, creator_user.telegram_user_id, "Q1", ["A", "B"], 0
    )

    # >=1 question: /done must succeed
    success, count = QuizService.finish_questions(db_session, creator_user.telegram_user_id)
    assert success is True
    assert count == 1


def test_cancel_draft_discards_quiz(db_session, creator_user):
    """/cancel completely removes active draft and draft quiz."""
    quiz, _ = QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    cancelled = QuizService.cancel_draft(db_session, creator_user.telegram_user_id)
    assert cancelled is True

    # Check quiz and draft are gone
    assert QuizRepository.get_by_id(db_session, quiz.id) is None
    assert DraftRepository.get_by_user_id(db_session, creator_user.id) is None

    # Cancelling when no draft exists returns False
    assert QuizService.cancel_draft(db_session, creator_user.telegram_user_id) is False


def test_publish_and_deep_link(db_session, creator_user):
    """Publishing draft creates unique quiz code and generates deep link."""
    QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    QuizService.set_title(db_session, creator_user.telegram_user_id, "NEET Zoology")
    QuizService.set_description(db_session, creator_user.telegram_user_id, "Final revision")
    QuestionService.add_native_poll_question(
        db_session, creator_user.telegram_user_id, "Q1", ["A", "B"], 0
    )
    QuizService.set_timer(db_session, creator_user.telegram_user_id, 45)
    QuizService.set_shuffle(db_session, creator_user.telegram_user_id, True, True)

    published_quiz = QuizService.publish_draft(db_session, creator_user.telegram_user_id)
    assert published_quiz.status == "PUBLISHED"
    assert published_quiz.quiz_code.startswith("QUIZ_")

    deep_link = QuizService.generate_deep_link("NeetQuizBot", published_quiz.quiz_code)
    assert deep_link == f"https://t.me/NeetQuizBot?start=quiz_{published_quiz.quiz_code}"


def test_reply_keyboard_parsers():
    """Verify timer, shuffle, and marking text parsers match button options."""
    from app.bot.handlers.creation_handlers import (
        parse_timer_text,
        parse_shuffle_text,
        parse_marking_text
    )

    # Timer parser
    assert parse_timer_text("10 sec") == 10
    assert parse_timer_text("15 sec") == 15
    assert parse_timer_text("30 sec") == 30
    assert parse_timer_text("45 sec") == 45
    assert parse_timer_text("1 min") == 60
    assert parse_timer_text("2 min") == 120
    assert parse_timer_text("3 min") == 180
    assert parse_timer_text("5 min") == 300
    assert parse_timer_text("No Timer") == 0

    # Shuffle parser
    assert parse_shuffle_text("🔀 Shuffle All") == (True, True)
    assert parse_shuffle_text("➡️ No Shuffle") == (False, False)
    assert parse_shuffle_text("No Shuffle") == (False, False)
    assert parse_shuffle_text("❓ Shuffle Questions") == (True, False)
    assert parse_shuffle_text("🔤 Shuffle Options") == (False, True)

    # Marking parser
    assert parse_marking_text("🎯 NEET Marking (+4 / -1)") == (4.0, -1.0)
    assert parse_marking_text("📝 General Marking (+1 / -1)") == (1.0, -1.0)
    assert parse_marking_text("✅ Simple Marking (+1 / 0)") == (1.0, 0.0)


def test_quiz_draft_step_states(db_session, creator_user):
    """Verify draft states transition correctly from questions -> timer -> shuffle -> marking -> publish."""
    QuizService.start_new_quiz(db_session, creator_user.telegram_user_id)
    QuizService.set_title(db_session, creator_user.telegram_user_id, "State Transition Test")
    QuizService.set_description(db_session, creator_user.telegram_user_id, "Test Desc")
    QuestionService.add_native_poll_question(
        db_session, creator_user.telegram_user_id, "Q1", ["A", "B"], 0
    )

    # Finish questions -> WAITING_TIMER
    success, _ = QuizService.finish_questions(db_session, creator_user.telegram_user_id)
    assert success is True
    _, state1 = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state1 == "WAITING_TIMER"

    # Set timer -> WAITING_SHUFFLE
    QuizService.set_timer(db_session, creator_user.telegram_user_id, 15)
    _, state2 = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state2 == "WAITING_SHUFFLE"

    # Set shuffle -> WAITING_MARKING
    QuizService.set_shuffle(db_session, creator_user.telegram_user_id, False, False)
    _, state3 = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state3 == "WAITING_MARKING"

    # Set marking -> READY_TO_PUBLISH
    QuizService.set_marking(db_session, creator_user.telegram_user_id, 4.0, -1.0, 0.0)
    _, state4 = QuizService.get_active_draft_state(db_session, creator_user.telegram_user_id)
    assert state4 == "READY_TO_PUBLISH"

    # Publish
    pub = QuizService.publish_draft(db_session, creator_user.telegram_user_id)
    assert pub.status == "PUBLISHED"
    assert pub.timer_seconds == 15
    assert pub.shuffle_questions is False
    assert pub.shuffle_options is False
    assert pub.correct_marks == 4.0
    assert pub.wrong_marks == -1.0
