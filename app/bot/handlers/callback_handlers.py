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
        try:
            await query.answer()
        except Exception:
            pass
        seconds = int(data.split(":", 1)[1])
        with get_db() as db:
            QuizService.set_timer(db, user.id, seconds)

        timer_display = f"{seconds} seconds" if seconds > 0 else "No Timer"
        try:
            await query.edit_message_text(
                text=f"⏱ Question timer set to: *{timer_display}*\n\n{t('shuffle_prompt')}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_shuffle_keyboard()
            )
        except Exception:
            pass
        return

    # 3. Shuffle Selection -> Prompt for Marking Scheme
    elif data.startswith("shuffle:"):
        try:
            await query.answer()
        except Exception:
            pass
        mode = data.split(":", 1)[1]
        shuffle_q = mode in ("all", "questions")
        shuffle_opt = mode in ("all", "options")

        with get_db() as db:
            QuizService.set_shuffle(db, user.id, shuffle_q, shuffle_opt)

        from app.bot.keyboards.inline import get_marking_keyboard
        try:
            await query.edit_message_text(
                text="⚖️ *Choose the marking scheme for this quiz:*\n\n"
                     "• *🎯 NEET Marking*: +4 Correct, -1 Wrong, 0 Skipped\n"
                     "• *🏥 NORCET Marking*: +1 Correct, -0.33 Wrong, 0 Skipped\n"
                     "• *✅ Simple Marking*: +1 Correct, 0 Wrong, 0 Skipped",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_marking_keyboard()
            )
        except Exception:
            pass
        return

    # 3b. Marking Selection & Publishing
    elif data.startswith("marking:"):
        try:
            await query.answer()
        except Exception:
            pass
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

        try:
            await query.message.delete()
        except Exception:
            pass

        from app.bot.handlers.creation_handlers import send_published_quiz_summary
        await send_published_quiz_summary(chat, quiz, bot_username)
        return

    # 3c. Edit Quiz Menu & Actions
    elif data.startswith("edit_quiz:"):
        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if not quiz:
                await query.answer("Quiz not found.", show_alert=True)
                return
            if quiz.creator.telegram_id != user.id:
                await query.answer("You can only edit your own quizzes.", show_alert=True)
                return

        from app.bot.keyboards.inline import get_edit_quiz_keyboard
        try:
            await query.edit_message_text(
                text=f"⚙️ *Edit Quiz Settings*\n\nQuiz: *{quiz.title}*\n\nSelect what you want to edit:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_edit_quiz_keyboard(quiz_code)
            )
        except Exception:
            await chat.send_message(
                text=f"⚙️ *Edit Quiz Settings*\n\nQuiz: *{quiz.title}*\n\nSelect what you want to edit:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_edit_quiz_keyboard(quiz_code)
            )
        return

    elif data.startswith("edit_title:"):
        quiz_code = data.split(":", 1)[1]
        context.user_data["editing_quiz_code"] = quiz_code
        context.user_data["editing_field"] = "title"
        await chat.send_message("📝 *Please send the new title for your quiz:*", parse_mode=ParseMode.MARKDOWN)
        return

    elif data.startswith("edit_desc:"):
        quiz_code = data.split(":", 1)[1]
        context.user_data["editing_quiz_code"] = quiz_code
        context.user_data["editing_field"] = "desc"
        await chat.send_message("📄 *Please send the new description for your quiz (or send /skip to remove description):*", parse_mode=ParseMode.MARKDOWN)
        return

    elif data.startswith("edit_timer:"):
        quiz_code = data.split(":", 1)[1]
        from app.bot.keyboards.inline import get_edit_timer_keyboard
        try:
            await query.edit_message_text(
                text="⏱ *Select a new timer per question:*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_edit_timer_keyboard(quiz_code)
            )
        except Exception:
            pass
        return

    elif data.startswith("ed_tm:"):
        parts = data.split(":")
        quiz_code = parts[1]
        seconds = int(parts[2])
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz and quiz.creator.telegram_id == user.id:
                quiz.timer_seconds = seconds
                db.commit()
                db.refresh(quiz)
                timer_display = f"{seconds} seconds" if seconds > 0 else "No Timer"
                await query.answer(f"Timer set to {timer_display}!")
                try:
                    await query.message.delete()
                except Exception:
                    pass
                from app.bot.handlers.creation_handlers import send_published_quiz_summary
                await send_published_quiz_summary(chat, quiz, bot_username)
        return

    elif data.startswith("edit_shuffle:"):
        quiz_code = data.split(":", 1)[1]
        from app.bot.keyboards.inline import get_edit_shuffle_keyboard
        try:
            await query.edit_message_text(
                text="🔀 *Select shuffle settings for this quiz:*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_edit_shuffle_keyboard(quiz_code)
            )
        except Exception:
            pass
        return

    elif data.startswith("ed_sh:"):
        parts = data.split(":")
        quiz_code = parts[1]
        mode = parts[2]
        shuffle_q = mode in ("all", "questions")
        shuffle_opt = mode in ("all", "options")
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz and quiz.creator.telegram_id == user.id:
                quiz.shuffle_questions = shuffle_q
                quiz.shuffle_options = shuffle_opt
                db.commit()
                db.refresh(quiz)
                await query.answer("Shuffle settings updated!")
                try:
                    await query.message.delete()
                except Exception:
                    pass
                from app.bot.handlers.creation_handlers import send_published_quiz_summary
                await send_published_quiz_summary(chat, quiz, bot_username)
        return

    elif data.startswith("edit_marking:"):
        quiz_code = data.split(":", 1)[1]
        from app.bot.keyboards.inline import get_edit_marking_keyboard
        try:
            await query.edit_message_text(
                text="⚖️ *Choose a new marking scheme for this quiz:*\n\n"
                     "• *🎯 NEET Marking*: +4 Correct, -1 Wrong, 0 Skipped\n"
                     "• *🏥 NORCET Marking*: +1 Correct, -0.33 Wrong, 0 Skipped\n"
                     "• *✅ Simple Marking*: +1 Correct, 0 Wrong, 0 Skipped",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_edit_marking_keyboard(quiz_code)
            )
        except Exception:
            pass
        return

    elif data.startswith("ed_mk:"):
        parts = data.split(":")
        quiz_code = parts[1]
        correct = float(parts[2])
        wrong = float(parts[3])
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz and quiz.creator.telegram_id == user.id:
                quiz.correct_marks = correct
                quiz.wrong_marks = wrong
                db.commit()
                db.refresh(quiz)
                await query.answer("Marking scheme updated!")
                try:
                    await query.message.delete()
                except Exception:
                    pass
                from app.bot.handlers.creation_handlers import send_published_quiz_summary
                await send_published_quiz_summary(chat, quiz, bot_username)
        return

    elif data.startswith("del_quiz:"):
        quiz_code = data.split(":", 1)[1]
        from app.bot.keyboards.inline import get_delete_confirm_keyboard
        try:
            await query.edit_message_text(
                text="⚠️ *Are you sure you want to delete this quiz?*\nThis action cannot be undone.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_delete_confirm_keyboard(quiz_code)
            )
        except Exception:
            pass
        return

    elif data.startswith("del_confirm:"):
        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz and quiz.creator.telegram_id == user.id:
                db.delete(quiz)
                db.commit()
                await query.edit_message_text("🗑 *Quiz has been deleted successfully.*", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.answer("Could not delete quiz.", show_alert=True)
        return

    elif data.startswith("back_to_quiz:"):
        quiz_code = data.split(":", 1)[1]
        with get_db() as db:
            quiz = QuizRepository.get_by_code(db, quiz_code)
            if quiz:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                from app.bot.handlers.creation_handlers import send_published_quiz_summary
                await send_published_quiz_summary(chat, quiz, bot_username)
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
        try:
            await query.answer()
        except Exception:
            pass
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
            else:
                avg_score = 0.0
                high_score = 0.0
                low_score = 0.0
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
