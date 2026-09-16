"""Inline callback query handlers."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.database.connection import get_db
from app.database.repositories.quiz_repo import QuizRepository
from app.services.quiz_service import QuizService
from app.services.attempt_service import AttemptService
from app.bot.keyboards.inline import (
    get_shuffle_keyboard,
    get_quiz_result_keyboard,
    get_quiz_intro_keyboard
)
from app.bot.keyboards.reply import get_remove_keyboard
from app.bot.handlers.quiz_handlers import send_next_question
from app.utils.localization import t
from app.utils.logger import logger


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route inline keyboard callback queries."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    data = query.data
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    bot_user = await context.bot.get_me()
    bot_username = bot_user.username or "quizbot"

    # 1. Menu shortcuts
    if data == "cmd:newquiz":
        with get_db() as db:
            quiz, status = QuizService.start_new_quiz(db, user.id, user.username, user.first_name)
            if status == "UNFINISHED_EXISTS":
                await chat.send_message(t("newquiz_unfinished"))
                return
        await chat.send_message(t("newquiz_prompt_title"), reply_markup=get_remove_keyboard())
        return

    elif data == "cmd:quizzes":
        from app.bot.handlers.commands import quizzes_command
        await quizzes_command(update, context)
        return

    elif data == "cmd:help":
        from app.bot.handlers.commands import help_command
        await help_command(update, context)
        return

    elif data == "cmd:start":
        from app.bot.handlers.commands import start_command
        await start_command(update, context)
        return

    # 2. Timer Selection
    elif data.startswith("timer:"):
        seconds = int(data.split(":", 1)[1])
        with get_db() as db:
            QuizService.set_timer(db, user.id, seconds)

        timer_display = f"{seconds} seconds" if seconds > 0 else "No Timer"
        await query.edit_message_text(
            text=f"⏱ Question timer set to: *{timer_display}*\n\n{t('shuffle_prompt')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_shuffle_keyboard()
        )
        return

    # 3. Shuffle Selection & Publishing
    elif data.startswith("shuffle:"):
        mode = data.split(":", 1)[1]
        shuffle_q = mode in ("all", "questions")
        shuffle_opt = mode in ("all", "options")

        with get_db() as db:
            QuizService.set_shuffle(db, user.id, shuffle_q, shuffle_opt)
            quiz = QuizService.publish_draft(db, user.id)

            if not quiz:
                # If already published (e.g. user double-clicked), fetch most recent quiz
                from app.database.repositories.user_repo import UserRepository
                user_obj = UserRepository.get_by_telegram_id(db, user.id)
                if user_obj:
                    quizzes = QuizRepository.get_by_creator(db, user_obj.id)
                    if quizzes and quizzes[0].status == "PUBLISHED":
                        quiz = quizzes[0]

            if not quiz:
                await chat.send_message("⚠️ Could not publish quiz. Please try again.")
                return

            quiz_title = quiz.title
            quiz_code = quiz.quiz_code
            timer_seconds = quiz.timer_seconds
            shuffle_questions = quiz.shuffle_questions
            shuffle_options = quiz.shuffle_options
            correct_marks = int(quiz.correct_marks)
            wrong_marks = int(quiz.wrong_marks)
            unattempted_marks = int(quiz.unattempted_marks)
            q_count = len(quiz.questions)

        share_url = QuizService.generate_deep_link(bot_username, quiz_code)
        timer_str = f"{timer_seconds} seconds" if timer_seconds > 0 else "No Timer"

        summary_text = t(
            "quiz_summary",
            title=quiz_title,
            count=q_count,
            timer=timer_str,
            shuffle_questions="Yes" if shuffle_questions else "No",
            shuffle_options="Yes" if shuffle_options else "No",
            correct_marks=correct_marks,
            wrong_marks=wrong_marks,
            unattempted_marks=unattempted_marks,
            share_url=share_url
        )

        try:
            await query.edit_message_text(
                text=summary_text,
                reply_markup=get_quiz_intro_keyboard(quiz_code, bot_username)
            )
        except Exception as e:
            logger.warning(f"edit_message_text error (possibly identical content): {e}")
            await chat.send_message(
                text=summary_text,
                reply_markup=get_quiz_intro_keyboard(quiz_code, bot_username)
            )
        return

    # 4. Start Quiz Attempt (Private)
    elif data.startswith("start_attempt:"):
        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            attempt, status = AttemptService.start_attempt(
                db=db,
                telegram_user_id=user.id,
                quiz_code=quiz_code,
                username=user.username,
                first_name=user.first_name
            )

        if status != "SUCCESS" or not attempt:
            await chat.send_message("⚠️ Could not start quiz. It may have no questions or be unavailable.")
            return

        await chat.send_message("🚀 Starting your quiz attempt! Get ready...")
        await send_next_question(context, chat.id, user.id, attempt.id)
        return

    # 4b. Start Group Quiz Attempt
    elif data.startswith("start_grp:"):
        import asyncio
        from app.services.group_quiz_service import GroupQuizService
        from app.bot.handlers.group_quiz_handlers import deliver_group_question

        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            session, status = GroupQuizService.get_or_create_session(db, quiz_code, chat.id)
            if status != "SUCCESS" or not session:
                await chat.send_message("⚠️ Could not start group quiz. It may have no questions or be unavailable.")
                return
            GroupQuizService.start_session(db, session.id)
            session_id = session.id

        await query.edit_message_text(
            text="🚀 *Group Quiz is starting now!* First question coming up in 3 seconds...",
            parse_mode=ParseMode.MARKDOWN
        )
        await asyncio.sleep(3)
        await deliver_group_question(context, chat.id, session_id)
        return

    # 5. Quiz Statistics
    elif data.startswith("stats:"):
        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if not quiz:
                await chat.send_message(t("quiz_not_found"))
                return

            completed_attempts = [a for a in quiz.attempts if a.status == "COMPLETED"]
            total_attempts = len(completed_attempts)
            if total_attempts > 0:
                scores = [a.score for a in completed_attempts]
                avg_score = round(sum(scores) / total_attempts, 2)
                high_score = max(scores)
                low_score = min(scores)
            total_questions = len(quiz.questions)
            quiz_title = quiz.title

        stats_msg = (
            f"📊 *Quiz Stats: {quiz_title}*\n\n"
            f"Total Questions: {total_questions}\n"
            f"Total Attempts: {total_attempts}\n"
            f"Average Score: {avg_score}\n"
            f"Highest Score: {high_score}\n"
            f"Lowest Score: {low_score}\n"
        )
        await chat.send_message(text=stats_msg, parse_mode=ParseMode.MARKDOWN)
        return
