"""Initial database schema migration.

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-15 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=10), server_default="en", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True)

    # Quizzes table
    op.create_table(
        "quizzes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_code", sa.String(length=32), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="DRAFT", nullable=False),
        sa.Column("timer_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("shuffle_questions", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("shuffle_options", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("correct_marks", sa.Float(), server_default="4.0", nullable=False),
        sa.Column("wrong_marks", sa.Float(), server_default="-1.0", nullable=False),
        sa.Column("unattempted_marks", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_quizzes_quiz_code", "quizzes", ["quiz_code"], unique=True)
    op.create_index("ix_quizzes_creator_id", "quizzes", ["creator_id"])
    op.create_index("ix_quizzes_status", "quizzes", ["status"])

    # Questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("telegram_poll_id", sa.String(length=128), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("correct_option_id", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("media_file_id", sa.String(length=255), nullable=True),
        sa.Column("media_type", sa.String(length=32), nullable=True),
        sa.Column("position", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("chapter", sa.String(length=100), nullable=True),
        sa.Column("difficulty", sa.String(length=32), nullable=True),
        sa.Column("tags", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("latex_content", sa.Text(), nullable=True),
        sa.Column("question_image", sa.String(length=255), nullable=True),
        sa.Column("option_images", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_questions_quiz_id", "questions", ["quiz_id"])
    op.create_index("ix_questions_telegram_poll_id", "questions", ["telegram_poll_id"])

    # Options table
    op.create_table(
        "options",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_index", sa.Integer(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_options_question_id", "options", ["question_id"])

    # Quiz Attempts table
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="IN_PROGRESS", nullable=False),
        sa.Column("current_question_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("wrong_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unattempted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_status", "quiz_attempts", ["status"])

    # Attempt Questions table
    op.create_table(
        "attempt_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("display_position", sa.Integer(), nullable=False),
        sa.Column("option_mapping", sa.JSON(), nullable=True),
        sa.Column("telegram_poll_id", sa.String(length=128), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_attempt_questions_attempt_id", "attempt_questions", ["attempt_id"])
    op.create_index("ix_attempt_questions_telegram_poll_id", "attempt_questions", ["telegram_poll_id"])

    # Attempt Answers table
    op.create_table(
        "attempt_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("marks_awarded", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ANSWERED", nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_attempt_answers_attempt_id", "attempt_answers", ["attempt_id"])

    # Creation Drafts table
    op.create_table(
        "creation_drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=64), server_default="WAITING_TITLE", nullable=False),
        sa.Column("pending_media_file_id", sa.String(length=255), nullable=True),
        sa.Column("pending_media_type", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id")
    )
    op.create_index("ix_creation_drafts_user_id", "creation_drafts", ["user_id"])
    op.create_index("ix_creation_drafts_quiz_id", "creation_drafts", ["quiz_id"])


def downgrade() -> None:
    op.drop_table("creation_drafts")
    op.drop_table("attempt_answers")
    op.drop_table("attempt_questions")
    op.drop_table("quiz_attempts")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_table("quizzes")
    op.drop_table("users")
