"""Bot command handlers."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.config import settings
from app.database.connection import get_db
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.quiz_repo import QuizRepository
from app.services.quiz_service import QuizService
from app.services.attempt_service import AttemptService
from app.bot.keyboards.inline import (
    get_start_keyboard,
    get_timer_keyboard,
    get_quiz_intro_keyboard,
    get_quiz_item_keyboard
)
from app.bot.keyboards.reply import get_remove_keyboard, get_timer_reply_keyboard
from app.utils.localization import t
from app.utils.logger import logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with support for deep links (/start quiz_<CODE>)."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    # Check for deep-linking parameter
    args = context.args or []
    if args and (args[0].startswith("quiz_") or args[0].startswith("quiz:")):
        quiz_code = args[0].replace("quiz_", "", 1).replace("quiz:", "", 1)
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if not quiz:
                await chat.send_message(t("quiz_not_found"))
                return

            q_count = len(quiz.questions)
            timer_text = f"{quiz.timer_seconds}s" if quiz.timer_seconds > 0 else "30s"
            description = quiz.description or "No description provided."

            # If inside a Telegram Group / Supergroup
            if chat.type in ["group", "supergroup"]:
                from app.bot.keyboards.inline import get_group_ready_keyboard
                from app.utils.branding import GLOBAL_PROMO_TEXT
                desc_text = f"\n{quiz.description}\n" if quiz.description else ""
                group_text = (
                    f"🎲 *Get ready for the quiz:*\n"
                    f"*{quiz.title}*\n"
                    f"{desc_text}\n"
                    f"🖊 *{q_count} questions* · ⏱ *{timer_text}* per question\n"
                    f"⚖️ Marking: *+{int(quiz.correct_marks)}* correct, *{int(quiz.wrong_marks)}* wrong\n\n"
                    f"Tap the button below when you are ready!\n\n"
                    f"──────────────────\n"
                    f"{GLOBAL_PROMO_TEXT}"
                )
                await chat.send_message(
                    text=group_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_group_ready_keyboard(quiz.quiz_code, 0)
                )
                return

            from app.utils.branding import GLOBAL_PROMO_TEXT
            intro_text = t(
                "participant_quiz_intro",
                title=quiz.title,
                description=description,
                count=q_count,
                correct=int(quiz.correct_marks),
                wrong=int(quiz.wrong_marks),
                unattempted=int(quiz.unattempted_marks),
                timer=timer_text
            )
            intro_text = f"{intro_text}\n\n──────────────────\n{GLOBAL_PROMO_TEXT}"

        bot_user = await context.bot.get_me()
        bot_username = bot_user.username or "akaxxh_bot"

        await chat.send_message(
            text=intro_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_quiz_intro_keyboard(quiz.quiz_code, bot_username)
        )
        return

    # Standard /start welcome message
    with get_db() as db:
        UserRepository.get_or_create(
            db=db,
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    bot_user = await context.bot.get_me()
    bot_username = bot_user.username or "akaxxh_bot"

    welcome_text = t("start_welcome")
    await chat.send_message(
        text=welcome_text,
        reply_markup=get_start_keyboard(bot_username)
    )


async def newquiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /newquiz command to start a new quiz creation session."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    with get_db() as db:
        quiz, status = QuizService.start_new_quiz(
            db=db,
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

        if status == "UNFINISHED_EXISTS":
            await chat.send_message(t("newquiz_unfinished"))
            return

    await chat.send_message(
        text=t("newquiz_prompt_title"),
        reply_markup=get_remove_keyboard()
    )


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /undo command to remove latest question from current draft."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    with get_db() as db:
        removed, count = QuizService.undo_last_question(db, user.id)

    if removed:
        await chat.send_message(f"{t('undo_success')} Current question count: {count}")
    else:
        await chat.send_message(t("undo_empty"))


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /done command to proceed to settings if at least 1 question is added."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    with get_db() as db:
        success, count = QuizService.finish_questions(db, user.id)

    if not success:
        await chat.send_message(t("done_need_questions"))
        return

    await chat.send_message(
        text=t("timer_prompt"),
        reply_markup=get_timer_reply_keyboard()
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command to discard active quiz draft."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    with get_db() as db:
        cancelled = QuizService.cancel_draft(db, user.id)

    if cancelled:
        await chat.send_message(
            text=t("cancel_success"),
            reply_markup=get_remove_keyboard()
        )
    else:
        await chat.send_message(t("cancel_no_active"))


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command to safely stop an active quiz attempt or session."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    stopped = False
    with get_db() as db:
        u = UserRepository.get_by_telegram_id(db, user.id)
        if u:
            active_attempt = AttemptService.start_attempt  # check active
            from app.database.repositories.attempt_repo import AttemptRepository
            att = AttemptRepository.get_active_attempt(db, u.id)
            if att:
                AttemptRepository.abandon_attempt(db, att.id)
                stopped = True

        if QuizService.cancel_draft(db, user.id):
            stopped = True

    if stopped:
        await chat.send_message(
            text=t("stop_success"),
            reply_markup=get_remove_keyboard()
        )
    else:
        await chat.send_message(t("stop_no_active"))


async def quizzes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quizzes (or /myquizzes) command."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    bot_user = await context.bot.get_me()
    bot_username = bot_user.username or "quizbot"

    with get_db() as db:
        quizzes = QuizService.get_user_quizzes(db, user.id)
        quiz_draft, state = QuizService.get_active_draft_state(db, user.id)

    if quiz_draft:
        await chat.send_message(t("newquiz_unfinished"))

    if not quizzes:
        await chat.send_message(t("quizzes_empty"))
        return

    await chat.send_message(t("quizzes_header"))
    for idx, q in enumerate(quizzes, 1):
        q_count = len(q.questions)
        timer_str = f"{q.timer_seconds} sec" if q.timer_seconds > 0 else "No Timer"
        item_text = t(
            "quizzes_item",
            index=idx,
            title=q.title,
            count=q_count,
            timer=timer_str,
            correct=int(q.correct_marks),
            wrong=int(q.wrong_marks),
            status=q.status
        )
        await chat.send_message(
            text=item_text,
            reply_markup=get_quiz_item_keyboard(q.quiz_code, bot_username)
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command to show creator or global bot statistics."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    is_owner = (not settings.ADMIN_USER_IDS) or (user.id in settings.ADMIN_USER_IDS)

    with get_db() as db:
        if is_owner:
            from sqlalchemy import func
            from app.database.models.user import User
            from app.database.models.quiz import Quiz
            from app.database.models.attempt import QuizAttempt
            from app.database.models.group_quiz import GroupQuizSession, GroupQuizParticipant

            total_groups = db.query(func.count(func.distinct(GroupQuizSession.chat_id))).scalar() or 0
            total_users = db.query(func.count(User.id)).scalar() or 0
            total_quizzes = db.query(func.count(Quiz.id)).scalar() or 0
            indiv_attempts = db.query(func.count(QuizAttempt.id)).scalar() or 0
            group_attempts = db.query(func.count(GroupQuizParticipant.id)).scalar() or 0
            total_attempts = indiv_attempts + group_attempts

            stats_text = (
                "📊 *BOT STATISTICS*\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥 *Total Groups ➔* {total_groups}\n"
                f"👤 *Total Users ➔* {total_users}\n"
                f"📝 *Total Quizzes ➔* {total_quizzes}\n"
                f"🎯 *Total Attempts ➔* {total_attempts}\n\n"
                "🚀 _Quiz Bot is growing fast!_\n"
                "*Keep sharing & creating quizzes* 💡"
            )
            await chat.send_message(text=stats_text, parse_mode=ParseMode.MARKDOWN)
        else:
            stats = QuizService.get_creator_stats(db, user.id)
            stats_text = (
                "📊 *Creator Statistics*\n\n"
                f"Total Quizzes: {stats['total_quizzes']}\n"
                f"Total Questions: {stats['total_questions']}\n"
                f"Total Attempts: {stats['total_attempts']}\n"
                f"Average Score: {stats['average_score']}\n"
                f"Highest Score: {stats['highest_score']}\n"
                f"Lowest Score: {stats['lowest_score']}\n"
                f"Average Percentage: {stats['average_percentage']}%\n\n"
                "_(Global bot statistics are restricted to the bot owner)_"
            )
            await chat.send_message(text=stats_text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    chat = update.effective_chat
    if chat:
        await chat.send_message(t("help_text"))


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang command for language readiness."""
    chat = update.effective_chat
    if chat:
        await chat.send_message(t("lang_prompt") + "\n\n1. English (Default)\n2. Hindi (Coming Soon)")
