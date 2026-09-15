"""Quiz creation flow handlers (title, description, pre-question media, native polls)."""

from telegram import Update
from telegram.constants import PollType
from telegram.ext import ContextTypes
from app.database.connection import get_db
from app.services.quiz_service import QuizService
from app.services.question_service import QuestionService
from app.bot.keyboards.reply import get_create_question_keyboard, get_remove_keyboard
from app.utils.localization import t
from app.utils.logger import logger


async def handle_creation_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input during quiz creation (title, description, pre-question text)."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if not user or not chat or not message or not message.text:
        return

    text = message.text.strip()
    if text.startswith("/") and text != "/skip":
        return  # Let command handlers process other slash commands

    with get_db() as db:
        quiz, state = QuizService.get_active_draft_state(db, user.id)
        if not quiz or not state:
            return

        if state == "WAITING_TITLE":
            QuizService.set_title(db, user.id, text)
            await chat.send_message(t("newquiz_prompt_description"))
            return

        elif state == "WAITING_DESCRIPTION":
            description = None if text.lower() == "/skip" else text
            QuizService.set_description(db, user.id, description)
            await chat.send_message(
                text=t("newquiz_first_question_prompt"),
                reply_markup=get_create_question_keyboard()
            )
            return

        elif state == "WAITING_QUESTIONS":
            # Text sent before question can be pre-question text/notes
            QuestionService.set_pending_media(
                db=db,
                telegram_user_id=user.id,
                media_file_id=text,
                media_type="text"
            )
            await chat.send_message(
                text="📝 Note received! It will be shown before your next question.\nNow click 'Create a question' below.",
                reply_markup=get_create_question_keyboard()
            )
            return


async def handle_prequestion_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photos, videos, documents sent before creating a question."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if not user or not chat or not message:
        return

    with get_db() as db:
        quiz, state = QuizService.get_active_draft_state(db, user.id)
        if not quiz or state != "WAITING_QUESTIONS":
            return

        media_file_id = None
        media_type = None

        if message.photo:
            media_file_id = message.photo[-1].file_id  # highest resolution
            media_type = "photo"
        elif message.video:
            media_file_id = message.video.file_id
            media_type = "video"
        elif message.animation:
            media_file_id = message.animation.file_id
            media_type = "animation"
        elif message.document:
            media_file_id = message.document.file_id
            media_type = "document"

        if media_file_id and media_type:
            QuestionService.set_pending_media(
                db=db,
                telegram_user_id=user.id,
                media_file_id=media_file_id,
                media_type=media_type
            )
            await chat.send_message(
                text=t("media_attached"),
                reply_markup=get_create_question_keyboard()
            )


async def handle_native_poll_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the native Telegram quiz poll created and sent by the user.
    Extracts question, options, correct_option_id, explanation, attaches pending media.
    """
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if not user or not chat or not message or not message.poll:
        return

    poll = message.poll
    # Ensure it is a quiz poll
    if poll.type != PollType.QUIZ and poll.type != "quiz":
        await chat.send_message(
            "⚠️ Please make sure to create a *Quiz* poll (not a regular poll) with a single correct answer.",
            reply_markup=get_create_question_keyboard()
        )
        return

    question_text = poll.question
    options_text = [opt.text for opt in poll.options]
    correct_option_id = poll.correct_option_id if poll.correct_option_id is not None else 0
    explanation = poll.explanation

    with get_db() as db:
        quiz, state = QuizService.get_active_draft_state(db, user.id)
        if not quiz or state != "WAITING_QUESTIONS":
            return

        question, total_count = QuestionService.add_native_poll_question(
            db=db,
            telegram_user_id=user.id,
            question_text=question_text,
            options=options_text,
            correct_option_id=correct_option_id,
            explanation=explanation,
            telegram_poll_id=poll.id,
            telegram_message_id=message.message_id
        )

        quiz_title = quiz.title

    msg = t("question_added", title=quiz_title, count=total_count)
    await chat.send_message(
        text=msg,
        reply_markup=get_create_question_keyboard()
    )
