"""Pytest fixtures and test database setup."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models.base import Base
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.quiz_repo import QuizRepository
from app.database.repositories.question_repo import QuestionRepository


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def creator_user(db_session):
    """Create a creator user fixture."""
    return UserRepository.get_or_create(
        db=db_session,
        telegram_user_id=111111111,
        username="quiz_creator",
        first_name="Dr. Creator"
    )


@pytest.fixture
def participant_user(db_session):
    """Create a participant student user fixture."""
    return UserRepository.get_or_create(
        db=db_session,
        telegram_user_id=222222222,
        username="neet_aspirant",
        first_name="Aakash"
    )


@pytest.fixture
def sample_quiz(db_session, creator_user):
    """Create a sample published NEET quiz with questions."""
    quiz = QuizRepository.create(
        db=db_session,
        creator_id=creator_user.id,
        title="NEET Biology - Cell Division",
        description="Practice test covering mitosis and meiosis."
    )
    # Add question 1 (correct is Mitochondria, index 1)
    QuestionRepository.add_question(
        db=db_session,
        quiz_id=quiz.id,
        question_text="Which organelle is known as the powerhouse of the cell?",
        options=["Ribosome", "Mitochondria", "Golgi apparatus", "Lysosome"],
        correct_option_id=1,
        explanation="Mitochondria produce ATP via cellular respiration."
    )
    # Add question 2 (correct is Prophase, index 0)
    QuestionRepository.add_question(
        db=db_session,
        quiz_id=quiz.id,
        question_text="During which stage of mitosis do chromosomes condense?",
        options=["Prophase", "Metaphase", "Anaphase", "Telophase"],
        correct_option_id=0,
        explanation="Chromatin condenses into visible chromosomes in prophase."
    )
    QuizRepository.update_settings(
        db=db_session,
        quiz_id=quiz.id,
        timer_seconds=30,
        shuffle_questions=True,
        shuffle_options=True,
        correct_marks=4.0,
        wrong_marks=-1.0,
        unattempted_marks=0.0
    )
    QuizRepository.publish(db_session, quiz.id)
    return quiz
