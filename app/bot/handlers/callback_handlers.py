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
    get_quiz_intro_keyboard,
    get_quiz_created_keyboard,
    get_group_ready_keyboard
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

    # 3. Shuffle Selection -> Prompt for Marking Scheme
    elif data.startswith("shuffle:"):
        mode = data.split(":", 1)[1]
        shuffle_q = mode in ("all", "questions")
        shuffle_opt = mode in ("all", "options")

        with get_db() as db:
            QuizService.set_shuffle(db, user.id, shuffle_q, shuffle_opt)

        from app.bot.keyboards.inline import get_marking_keyboard
        await query.edit_message_text(
            text="⚖️ *Choose the marking scheme for this quiz:*\n\n"
                 "• *🎯 NEET Marking*: +4 Correct, -1 Wrong, 0 Skipped\n"
                 "• *📝 General Marking*: +1 Correct, -1 Wrong, 0 Skipped\n"
                 "• *✅ Simple Marking*: +1 Correct, 0 Wrong, 0 Skipped",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_marking_keyboard()
        )
        return

    # 3b. Marking Selection & Publishing
    elif data.startswith("marking:"):
        parts = data.split(":")
        correct = float(parts[1])
        wrong = float(parts[2])

        with get_db() as db:
            QuizService.set_marking(db, user.id, correct, wrong, 0.0)
            quiz = QuizService.publish_draft(db, user.id)

            if not quiz:
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
            correct_marks = int(quiz.correct_marks) if quiz.correct_marks.is_integer() else quiz.correct_marks
            wrong_marks = int(quiz.wrong_marks) if quiz.wrong_marks.is_integer() else quiz.wrong_marks
            unattempted_marks = int(quiz.unattempted_marks)
            q_count = len(quiz.questions)

        timer_str = f"{timer_seconds} sec" if timer_seconds > 0 else "no timer"
        shuffle_str = "no shuffle"
        if shuffle_questions and shuffle_options:
            shuffle_str = "shuffle all"
        elif shuffle_questions:
            shuffle_str = "shuffle questions"
        elif shuffle_options:
            shuffle_str = "shuffle options"

        desc_block = f"{quiz.description}\n\n" if quiz.description else ""
        attempts_str = f" {len(quiz.attempts)} people answered" if quiz.attempts else ""
        clean_bot = (bot_username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")

        summary_text = (
            "👍 *Quiz created.*\n\n"
            f"*{quiz_title}*{attempts_str}\n\n"
            f"{desc_block}"
            f"🖊 *{q_count} questions* · ⏱ *{timer_str}* · ⬇️ *{shuffle_str}*\n\n"
            "*External sharing link:*\n"
            f"t.me/{clean_bot}?start=quiz_{quiz_code}"
        )

        try:
            await query.edit_message_text(
                text=summary_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_quiz_created_keyboard(quiz_code, bot_username)
            )
        except Exception as e:
            logger.warning(f"edit_message_text error: {e}")
            await chat.send_message(
                text=summary_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_quiz_created_keyboard(quiz_code, bot_username)
            )
        return

    # 3c. Edit Quiz
    elif data.startswith("edit_quiz:"):
        await query.answer("✏️ To edit this quiz or create a new one, send /newquiz.", show_alert=True)
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

    # 4b. Start Group Quiz Attempt with "I'm ready!" and Live Countdown
    elif data.startswith("grp_ready:") or data.startswith("start_grp:"):
        import asyncio
        from app.services.group_quiz_service import GroupQuizService
        from app.bot.handlers.group_quiz_handlers import deliver_group_question

        quiz_code = data.split(":", 1)[1]
        chat_data = context.chat_data
        ready_users = chat_data.setdefault(f"ready_{quiz_code}", set())
        ready_users.add(user.id)
        ready_count = len(ready_users)

        # Update ready button count on message
        try:
            await query.edit_message_reply_markup(
                reply_markup=get_group_ready_keyboard(quiz_code, ready_count)
            )
        except Exception:
            pass

        # If countdown already initiated in this group, just acknowledge
        if chat_data.get(f"countdown_{quiz_code}"):
            await query.answer(f"✋ You are ready! ({ready_count} participants ready)", show_alert=False)
            return

        # Start countdown immediately with first ready person
        chat_data[f"countdown_{quiz_code}"] = True
        await query.answer("✋ You are ready! Starting countdown...", show_alert=False)

        with get_db() as db:
            session, status = GroupQuizService.get_or_create_session(db, quiz_code, chat.id)
            if status != "SUCCESS" or not session:
                chat_data[f"countdown_{quiz_code}"] = False
                await chat.send_message("⚠️ Could not start group quiz. It may have no questions or be unavailable.")
                return
            GroupQuizService.start_session(db, session.id)
            session_id = session.id
            quiz_obj = session.quiz
            quiz_title = quiz_obj.title if quiz_obj else "Quiz"

        # 3.. 2.. 1.. Live Countdown
        for remaining in [3, 2, 1]:
            try:
                await query.edit_message_text(
                    text=f"🎲 *Get ready for the quiz: {quiz_title}*\n\n"
                         f"🚀 *{len(ready_users)} participant(s) ready!*\n\n"
                         f"⏱ *The quiz will begin in {remaining}...*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass
            await asyncio.sleep(1)

        try:
            await query.edit_message_text(
                text=f"🎲 *Quiz: {quiz_title}*\n\n🚀 *Starting now! Good luck to all participants!*",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass

        await asyncio.sleep(1)
        chat_data[f"countdown_{quiz_code}"] = False
        chat_data[f"ready_{quiz_code}"] = set()
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
