"""Quiz creation flow handlers (title, description, pre-question media, native polls, step-by-step reply keyboard transitions)."""

import re
from typing import Tuple, Optional
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions
)
from telegram.constants import ParseMode, PollType
from telegram.ext import ContextTypes
from app.config import settings
from app.database.connection import get_db
from app.services.quiz_service import QuizService
from app.services.question_service import QuestionService
from app.bot.keyboards.reply import (
    get_create_question_keyboard,
    get_timer_reply_keyboard,
    get_shuffle_reply_keyboard,
    get_marking_reply_keyboard,
    get_remove_keyboard
)
from app.bot.keyboards.inline import get_quiz_created_keyboard
from app.utils.branding import GLOBAL_PROMO_TEXT, get_promo_keyboard_row
from app.utils.localization import t
from app.utils.logger import logger


def parse_timer_text(text: str) -> int:
    """Parse timer seconds from reply keyboard button or user text."""
    t_clean = text.lower().strip()
    if "no" in t_clean or "none" in t_clean or "off" in t_clean:
        return 0
    digits = re.findall(r"\d+", t_clean)
    if digits:
        val = int(digits[0])
        if "min" in t_clean:
            return val * 60
        return val
    return 30


def parse_shuffle_text(text: str) -> Tuple[bool, bool]:
    """Parse shuffle options from reply keyboard button or user text."""
    t_clean = text.lower().strip()
    if "no shuffle" in t_clean or "don't" in t_clean or "none" in t_clean:
        return False, False
    if "question" in t_clean:
        return True, False
    if "option" in t_clean:
        return False, True
    return True, True  # Default: Shuffle All


def parse_marking_text(text: str) -> Tuple[float, float]:
    """Parse marking scheme from reply keyboard button or user text."""
    t_clean = text.lower().strip()
    if "norcet" in t_clean or "0.33" in t_clean or "-0.33" in t_clean:
        return 1.0, -0.33
    if "simple" in t_clean or "+1 / 0" in t_clean or "+1/0" in t_clean:
        return 1.0, 0.0
    return 4.0, -1.0  # Default NEET (+4 / -1)


async def send_published_quiz_summary(chat, quiz, bot_username: str) -> None:
    """
    Clears the bottom reply keyboard and sends the official rich card matching Image 1.
    """
    # 1. Close and remove the bottom reply keyboard so normal chat keyboard opens up
    try:
        rm = await chat.send_message("✨ Quiz ready!", reply_markup=get_remove_keyboard())
        await rm.delete()
    except Exception:
        pass

    q_count = len(quiz.questions)
    timer_str = f"{quiz.timer_seconds} sec" if quiz.timer_seconds > 0 else "no timer"
    shuffle_str = "no shuffle"
    if quiz.shuffle_questions and quiz.shuffle_options:
        shuffle_str = "shuffle all"
    elif quiz.shuffle_questions:
        shuffle_str = "shuffle questions"
    elif quiz.shuffle_options:
        shuffle_str = "shuffle options"

    attempts_count = len(quiz.attempts) if quiz.attempts else 0
    attempts_str = f" {attempts_count} people answered" if attempts_count > 0 else ""

    def escape_md(val: str) -> str:
        if not val:
            return ""
        for c in ("_", "*", "`", "["):
            val = val.replace(c, f"\\{c}")
        return val

    clean_bot = (bot_username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")
    safe_title = escape_md(quiz.title)
    safe_desc = f"{escape_md(quiz.description)}\n\n" if quiz.description else ""
    safe_link = f"t.me/{escape_md(clean_bot)}?start=quiz\\_{escape_md(quiz.quiz_code)}"

    summary_text = (
        "👍 *Quiz created.*\n\n"
        f"*{safe_title}*{attempts_str}\n\n"
        f"{safe_desc}"
        f"🖊 *{q_count} questions* · ⏱ *{timer_str}* · ⬇️ *{shuffle_str}*\n\n"
        "*External sharing link:*\n"
        f"{safe_link}"
    )

    try:
        await chat.send_message(
            text=summary_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_quiz_created_keyboard(quiz.quiz_code, bot_username),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    except Exception as e:
        logger.warning(f"send_published_quiz_summary markdown fallback: {e}")
        plain_desc = f"{quiz.description}\n\n" if quiz.description else ""
        plain_summary = (
            "👍 Quiz created.\n\n"
            f"{quiz.title}{attempts_str}\n\n"
            f"{plain_desc}"
            f"🖊 {q_count} questions · ⏱ {timer_str} · ⬇️ {shuffle_str}\n\n"
            "External sharing link:\n"
            f"t.me/{clean_bot}?start=quiz_{quiz.quiz_code}"
        )
        await chat.send_message(
            text=plain_summary,
            reply_markup=get_quiz_created_keyboard(quiz.quiz_code, bot_username),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )


async def handle_creation_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input during quiz creation (title, description, settings) and quiz share detection."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if not user or not chat or not message or not message.text:
        return

    text = message.text.strip()
    bot_user = await context.bot.get_me()
    bot_username = (bot_user.username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")

    # 1. Detect if a user or group forwarded / typed a quiz code to share:
    # e.g. "@akaxxh_bot quiz:EhCSIDrH", "quiz:EhCSIDrH", "quiz_EhCSIDrH", "/quiz EhCSIDrH"
    share_code = None
    lower_text = text.lower()
    if lower_text.startswith(f"@{bot_username.lower()} quiz:") or lower_text.startswith("quiz:"):
        share_code = text.split("quiz:", 1)[1].strip().split()[0]
    elif lower_text.startswith(f"@{bot_username.lower()} quiz_") or lower_text.startswith("quiz_"):
        share_code = text.split("quiz_", 1)[1].strip().split()[0]
    elif lower_text.startswith("/quiz"):
        parts = text.split(None, 1)
        if len(parts) > 1:
            share_code = parts[1].strip()

    if share_code:
        from app.database.repositories.quiz_repo import QuizRepository
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, share_code)
            if quiz and quiz.status == "PUBLISHED":
                q_count = len(quiz.questions)
                timer_text = f"{quiz.timer_seconds} sec" if quiz.timer_seconds > 0 else "No Timer"
                desc_text = f"{quiz.description}\n\n" if quiz.description else ""
                attempts_count = len(quiz.attempts) if quiz.attempts else 0
                answered_str = f" {attempts_count} people answered" if attempts_count > 0 else ""

                card_text = (
                    f"🎲 *Quiz '{quiz.title}'*{answered_str}\n\n"
                    f"{desc_text}"
                    f"🖊 *{q_count} questions* · ⏱ *{timer_text}*\n\n"
                    f"──────────────────\n"
                    f"{GLOBAL_PROMO_TEXT}"
                )
                keyboard = [
                    [InlineKeyboardButton("Start this quiz", url=f"https://t.me/{bot_username}?start=quiz_{quiz.quiz_code}")],
                    [InlineKeyboardButton("Start quiz in group", url=f"https://t.me/{bot_username}?startgroup=quiz_{quiz.quiz_code}")],
                    [InlineKeyboardButton("Share quiz", switch_inline_query=f"quiz:{quiz.quiz_code}")],
                    get_promo_keyboard_row()
                ]
                await message.reply_text(
                    text=card_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )
                return

    # Check if user is editing title or description of an existing quiz
    if context.user_data.get("editing_quiz_code"):
        quiz_code = context.user_data.pop("editing_quiz_code")
        field = context.user_data.pop("editing_field", None)
        from app.database.repositories.quiz_repo import QuizRepository
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz and quiz.creator.telegram_id == user.id:
                if field == "title":
                    quiz.title = text
                    db.commit()
                    db.refresh(quiz)
                    await chat.send_message(f"✅ Title updated to: *{quiz.title}*", parse_mode=ParseMode.MARKDOWN)
                    await send_published_quiz_summary(chat, quiz, bot_username)
                    return
                elif field == "desc":
                    new_desc = None if text.strip().lower() in ("/skip", "skip") else text.strip()
                    quiz.description = new_desc
                    db.commit()
                    db.refresh(quiz)
                    await chat.send_message("✅ Description updated!", parse_mode=ParseMode.MARKDOWN)
                    await send_published_quiz_summary(chat, quiz, bot_username)
                    return

    # Skip slash commands so standard command handlers process them
    if text.startswith("/") and text != "/skip":
        return

    # 2. Universal reply buttons for creation flow
    if text in ("🏁 Done", "Done"):
        from app.bot.handlers.commands import done_command
        await done_command(update, context)
        return

    if text in ("↩️ Undo", "Undo"):
        from app.bot.handlers.commands import undo_command
        await undo_command(update, context)
        return

    if text in ("❌ Cancel", "Cancel"):
        from app.bot.handlers.commands import cancel_command
        await cancel_command(update, context)
        return

    if text in ("➕ Create a question", "Create a question"):
        await chat.send_message(
            "Tap '➕ Create a question' below to compose a native Telegram quiz poll:",
            reply_markup=get_create_question_keyboard()
        )
        return

    # 3. Handle active quiz draft states
    with get_db() as db:
        quiz, state = QuizService.get_active_draft_state(db, user.id)
        if not quiz or not state:
            return

        if state == "WAITING_TITLE":
            QuizService.set_title(db, user.id, text)
            await chat.send_message(t("newquiz_prompt_description"))
            return

        elif state == "WAITING_DESCRIPTION":
            description = None if text.strip().lower() in ("/skip", "skip") else text.strip()
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

        elif state == "WAITING_TIMER":
            seconds = parse_timer_text(text)
            QuizService.set_timer(db, user.id, seconds)
            timer_display = f"{seconds} seconds" if seconds > 0 else "No Timer"
            await chat.send_message(
                text=f"⏱ Question timer set to: *{timer_display}*\n\n{t('shuffle_prompt')}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_shuffle_reply_keyboard()
            )
            return

        elif state == "WAITING_SHUFFLE":
            shuffle_q, shuffle_opt = parse_shuffle_text(text)
            QuizService.set_shuffle(db, user.id, shuffle_q, shuffle_opt)
            await chat.send_message(
                text="⚖️ *Choose the marking scheme for this quiz:*\n\n"
                     "• *🎯 NEET Marking*: +4 Correct, -1 Wrong, 0 Skipped\n"
                     "• *🏥 NORCET Marking*: +1 Correct, -0.33 Wrong, 0 Skipped\n"
                     "• *✅ Simple Marking*: +1 Correct, 0 Wrong, 0 Skipped",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_marking_reply_keyboard()
            )
            return

        elif state == "WAITING_MARKING":
            correct, wrong = parse_marking_text(text)
            QuizService.set_marking(db, user.id, correct, wrong, 0.0)
            published_quiz = QuizService.publish_draft(db, user.id)
            if not published_quiz:
                from app.database.repositories.quiz_repo import QuizRepository
                from app.database.repositories.user_repo import UserRepository
                user_obj = UserRepository.get_by_telegram_id(db, user.id)
                if user_obj:
                    quizzes = QuizRepository.get_by_creator(db, user_obj.id)
                    if quizzes and quizzes[0].status == "PUBLISHED":
                        published_quiz = quizzes[0]

            if published_quiz:
                await send_published_quiz_summary(chat, published_quiz, bot_username)
            else:
                await chat.send_message("⚠️ Could not publish quiz. Please try again.", reply_markup=get_remove_keyboard())
            return


async def handle_quiz_share_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quiz <CODE> command."""
    await handle_creation_text(update, context)


async def handle_skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skip command for quiz description or editing."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    bot_user = await context.bot.get_me()
    bot_username = (bot_user.username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")

    # 1. Check if user is editing an existing quiz description
    if context.user_data.get("editing_field") == "desc":
        quiz_code = context.user_data.pop("editing_quiz_code", None)
        context.user_data.pop("editing_field", None)
        if quiz_code:
            from app.database.repositories.quiz_repo import QuizRepository
            with get_db() as db:
                quiz = QuizRepository.get_by_code(db, quiz_code)
                if quiz and quiz.creator.telegram_id == user.id:
                    quiz.description = None
                    db.commit()
                    db.refresh(quiz)
                    await chat.send_message("✅ Description cleared!")
                    await send_published_quiz_summary(chat, quiz, bot_username)
                    return

    # 2. Check if user is in quiz creation flow at WAITING_DESCRIPTION
    with get_db() as db:
        quiz, state = QuizService.get_active_draft_state(db, user.id)
        if quiz and state == "WAITING_DESCRIPTION":
            QuizService.set_description(db, user.id, None)
            await chat.send_message(
                text=t("newquiz_first_question_prompt"),
                reply_markup=get_create_question_keyboard()
            )
            return

    await chat.send_message("Nothing to skip right now.")


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
