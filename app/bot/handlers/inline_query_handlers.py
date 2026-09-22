"""Inline query handler for rich quiz sharing via @bot_name."""

import hashlib
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.config import settings
from app.database.connection import get_db
from app.database.repositories.quiz_repo import QuizRepository
from app.utils.logger import logger


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries like @bot_username quiz:CODE or search query."""
    inline_query = update.inline_query
    if not inline_query:
        return

    raw_query = inline_query.query.strip()
    bot_user = await context.bot.get_me()
    clean_bot = (bot_user.username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")

    # Extract quiz code if prefixed with quiz: or quiz_
    quiz_code = raw_query
    if raw_query.startswith("quiz:"):
        quiz_code = raw_query.replace("quiz:", "", 1).strip()
    elif raw_query.startswith("quiz_"):
        quiz_code = raw_query.replace("quiz_", "", 1).strip()

    results = []
    with get_db() as db:
        quizzes = []
        if quiz_code:
            q = QuizRepository.get_by_code(db, quiz_code)
            if q and q.status == "PUBLISHED":
                quizzes.append(q)

        # If not found by exact code, search user's quizzes or published quizzes
        if not quizzes:
            user_id = inline_query.from_user.id
            from app.database.repositories.user_repo import UserRepository
            u = UserRepository.get_by_telegram_id(db, user_id)
            if u:
                user_quizzes = QuizRepository.get_by_creator(db, u.id)
                published = [item for item in user_quizzes if item.status == "PUBLISHED"]
                if raw_query:
                    quizzes = [item for item in published if raw_query.lower() in item.title.lower()][:10]
                else:
                    quizzes = published[:10]

        for quiz in quizzes:
            q_count = len(quiz.questions)
            timer_text = f"{quiz.timer_seconds} sec" if quiz.timer_seconds > 0 else "No Timer"
            desc_text = f"{quiz.description}\n\n" if quiz.description else ""
            attempts_count = len(quiz.attempts)
            answered_str = f" {attempts_count} people answered" if attempts_count > 0 else ""

            from app.utils.branding import GLOBAL_PROMO_TEXT, get_promo_keyboard_row

            # Message content matching Image 1:
            # 🎲 Quiz 'NEET QUIZ BY ...'
            # [description]
            # 🖊 21 questions · ⏱ 15 sec
            message_text = (
                f"🎲 *Quiz '{quiz.title}'*{answered_str}\n\n"
                f"{desc_text}"
                f"🖊 *{q_count} questions* · ⏱ *{timer_text}*"
            )

            # Keyboard matching Image 1 with promo buttons:
            keyboard = [
                [InlineKeyboardButton("Start this quiz", url=f"https://t.me/{clean_bot}?start=quiz_{quiz.quiz_code}")],
                [InlineKeyboardButton("Start quiz in group", url=f"https://t.me/{clean_bot}?startgroup=quiz_{quiz.quiz_code}")],
                [InlineKeyboardButton("Share quiz", switch_inline_query=f"quiz:{quiz.quiz_code}")],
                get_promo_keyboard_row()
            ]

            result_id = hashlib.md5(f"{quiz.quiz_code}_{quiz.id}".encode()).hexdigest()
            results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"Quiz '{quiz.title}'",
                    description=f"{q_count} questions · {timer_text}",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode=ParseMode.MARKDOWN,
                        link_preview_options=LinkPreviewOptions(is_disabled=True)
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            )

    try:
        await inline_query.answer(results, cache_time=1, is_personal=True)
    except Exception as e:
        logger.error(f"Error answering inline query: {e}")
