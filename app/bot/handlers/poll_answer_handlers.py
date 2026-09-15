"""Telegram poll_answer update handler with idempotency and score evaluation."""

from telegram import Update
from telegram.ext import ContextTypes
from app.database.connection import get_db
from app.database.repositories.attempt_repo import AttemptRepository
from app.services.attempt_service import AttemptService
from app.services.timer_service import TimerService
from app.bot.handlers.quiz_handlers import send_next_question, send_quiz_results
from app.utils.logger import logger


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle participant poll answer update.
    Ensures idempotency, cancels server timer, awards score, and triggers next question.
    """
    poll_answer = update.poll_answer
    if not poll_answer or not poll_answer.user:
        return

    # Check if participant selected an option
    if not poll_answer.option_ids:
        return  # Option was retracted

    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    selected_option_index = poll_answer.option_ids[0]

    with get_db() as db:
        aq = AttemptRepository.get_attempt_question_by_poll_id(db, poll_id)
        if not aq:
            return

        attempt_id = aq.attempt_id
        attempt_question_id = aq.id

        # 1. Cancel pending server timer for this question
        TimerService.cancel_question_timeout(
            context=context,
            attempt_id=attempt_id,
            attempt_question_id=attempt_question_id
        )

        # 2. Process participant answer idempotently
        answer, is_complete, attempt = AttemptService.handle_poll_answer(
            db=db,
            poll_id=poll_id,
            telegram_user_id=user_id,
            selected_option_index=selected_option_index
        )

    if not answer or not attempt:
        return

    # 3. Deliver next question or show final results
    if is_complete:
        await send_quiz_results(context, user_id, attempt_id)
    else:
        await send_next_question(context, user_id, user_id, attempt_id)
