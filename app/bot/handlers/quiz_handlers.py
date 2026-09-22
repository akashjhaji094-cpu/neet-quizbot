"""Participant quiz execution, poll delivery, and final results handlers."""

from telegram.constants import ParseMode, PollType
from telegram.ext import ContextTypes
from app.database.connection import get_db
from app.database.repositories.attempt_repo import AttemptRepository
from app.services.attempt_service import AttemptService
from app.services.scoring_service import ScoringService
from app.services.timer_service import TimerService
from app.bot.keyboards.inline import get_quiz_result_keyboard
from app.bot.keyboards.reply import get_remove_keyboard
from app.utils.localization import t
from app.utils.logger import logger


async def on_question_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback fired when a question timer expires on the server."""
    job_data = context.job.data if context.job else None
    if not job_data:
        return

    chat_id = job_data["chat_id"]
    attempt_id = job_data["attempt_id"]
    attempt_question_id = job_data["attempt_question_id"]

    with get_db() as db:
        answer, is_complete, attempt = AttemptService.handle_timeout(
            db=db,
            attempt_id=attempt_id,
            attempt_question_id=attempt_question_id
        )

    if not answer:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=t("question_timeout")
    )

    if is_complete:
        await send_quiz_results(context, chat_id, attempt_id)
    else:
        user_tid = attempt.user.telegram_user_id if attempt and attempt.user else chat_id
        await send_next_question(context, chat_id, user_tid, attempt_id)


async def send_next_question(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_telegram_id: int,
    attempt_id: int
) -> None:
    """Fetch and deliver the next question for an ongoing attempt."""
    with get_db() as db:
        payload = AttemptService.get_current_question(db, attempt_id)

    if not payload:
        # All questions answered or attempt finished
        await send_quiz_results(context, chat_id, attempt_id)
        return

    # 1. Send pre-question media if attached
    media_file = payload.get("media_file_id")
    media_type = payload.get("media_type")
    if media_file and media_type:
        try:
            if media_type == "photo":
                await context.bot.send_photo(chat_id=chat_id, photo=media_file)
            elif media_type == "video":
                await context.bot.send_video(chat_id=chat_id, video=media_file)
            elif media_type == "animation":
                await context.bot.send_animation(chat_id=chat_id, animation=media_file)
            elif media_type == "document":
                await context.bot.send_document(chat_id=chat_id, document=media_file)
            elif media_type == "text":
                await context.bot.send_message(chat_id=chat_id, text=f"ℹ️ Note:\n{media_file}")
        except Exception as e:
            logger.error(f"Error sending pre-question media: {e}")

    # 2. Send Telegram native quiz poll
    timer_seconds = payload.get("timer_seconds", 0)
    open_period = timer_seconds if (timer_seconds and 5 <= timer_seconds <= 600) else None

    try:
        poll_msg = await context.bot.send_poll(
            chat_id=chat_id,
            question=payload["question_text"],
            options=payload["options"],
            type=PollType.QUIZ,
            is_anonymous=False,
            correct_option_id=payload["correct_option_id"],
            explanation=payload["explanation"],
            open_period=open_period
        )

        with get_db() as db:
            AttemptService.record_poll_sent(
                db=db,
                attempt_question_id=payload["attempt_question_id"],
                poll_id=poll_msg.poll.id,
                message_id=poll_msg.message_id,
                deadline=payload["deadline"]
            )

        # 3. Schedule server-side timeout if timer enabled
        if timer_seconds and timer_seconds > 0:
            TimerService.schedule_question_timeout(
                context=context,
                chat_id=chat_id,
                attempt_id=attempt_id,
                attempt_question_id=payload["attempt_question_id"],
                timer_seconds=timer_seconds,
                callback_coroutine=on_question_timeout
            )

    except Exception as e:
        logger.error(f"Error sending quiz poll: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Failed to deliver question {payload['display_position']}. Moving forward..."
        )


async def send_quiz_results(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    attempt_id: int
) -> None:
    """Display final NEET score card and action buttons."""
    with get_db() as db:
        attempt = AttemptRepository.get_by_id(db, attempt_id)
        if not attempt:
            return

        quiz = attempt.quiz
        bot_user = await context.bot.get_me()
        bot_username = bot_user.username or "quizbot"

        score_res = ScoringService.calculate_score(
            correct_count=attempt.correct_count,
            wrong_count=attempt.wrong_count,
            unattempted_count=attempt.unattempted_count,
            correct_marks=quiz.correct_marks,
            wrong_marks=quiz.wrong_marks,
            unattempted_marks=quiz.unattempted_marks
        )

        card_text = t(
            "quiz_completed",
            title=quiz.title,
            total=score_res.total_questions,
            correct=score_res.correct_count,
            wrong=score_res.wrong_count,
            unattempted=score_res.unattempted_count,
            correct_marks_total=int(score_res.correct_marks_total),
            wrong_marks_total=int(score_res.wrong_marks_total),
            score=int(score_res.score) if score_res.score.is_integer() else score_res.score,
            max_score=int(score_res.max_score) if score_res.max_score.is_integer() else score_res.max_score,
            percentage=score_res.percentage
        )

        quiz_code = quiz.quiz_code

    await context.bot.send_message(
        chat_id=chat_id,
        text=card_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_quiz_result_keyboard(quiz_code, bot_username)
    )
