"""Group Quiz execution, poll dispatching, and leaderboard display."""

import asyncio
from telegram.constants import ParseMode, PollType
from telegram.ext import ContextTypes
from app.database.connection import get_db
from app.services.group_quiz_service import GroupQuizService
from app.utils.logger import logger


async def on_group_question_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback fired when the timer for a group question expires."""
    job_data = context.job.data if context.job else None
    if not job_data:
        return

    chat_id = job_data["chat_id"]
    session_id = job_data["session_id"]

    with get_db() as db:
        is_finished, session = GroupQuizService.advance_question_or_finish(db, session_id)

    if is_finished:
        await send_group_leaderboard(context, chat_id, session_id)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⌛ Time's up! Next question coming up..."
        )
        await asyncio.sleep(2)
        await deliver_group_question(context, chat_id, session_id)


async def deliver_group_question(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    session_id: int
) -> None:
    """Send the current question to the group as a native quiz poll."""
    with get_db() as db:
        payload = GroupQuizService.get_current_question_payload(db, session_id)

    if not payload:
        await send_group_leaderboard(context, chat_id, session_id)
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
            logger.error(f"Error sending group pre-question media: {e}")

    # 2. Send Telegram native quiz poll
    timer_seconds = payload.get("timer_seconds", 30)
    open_period = timer_seconds if (5 <= timer_seconds <= 600) else 30
    q_title = f"[{payload['display_position']}/{payload['total_questions']}] {payload['question_text']}"

    try:
        poll_msg = await context.bot.send_poll(
            chat_id=chat_id,
            question=q_title,
            options=payload["options"],
            type=PollType.QUIZ,
            is_anonymous=False,
            correct_option_id=payload["correct_option_id"],
            explanation=payload["explanation"],
            open_period=open_period
        )

        with get_db() as db:
            GroupQuizService.record_poll_sent(db, session_id, poll_msg.poll.id)

        # 3. Schedule timeout job
        if context.job_queue:
            context.job_queue.run_once(
                callback=on_group_question_timeout,
                when=open_period,
                chat_id=chat_id,
                name=f"grp_timer_{session_id}_{payload['question_id']}",
                data={"chat_id": chat_id, "session_id": session_id}
            )

    except Exception as e:
        logger.error(f"Error sending group quiz poll: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Failed to send question {payload['display_position']}. Moving forward..."
        )
        with get_db() as db:
            is_fin, _ = GroupQuizService.advance_question_or_finish(db, session_id)
        if is_fin:
            await send_group_leaderboard(context, chat_id, session_id)
        else:
            await deliver_group_question(context, chat_id, session_id)


async def send_group_leaderboard(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    session_id: int
) -> None:
    """Construct and post the final leaderboard in the group."""
    with get_db() as db:
        data = GroupQuizService.generate_leaderboard_data(db, session_id)

    title = data["quiz_title"]
    rankings = data["rankings"]
    total_participants = data["total_participants"]
    total_q = data["total_questions"]

    if not rankings:
        text = (
            f"🏁 *QUIZ COMPLETE*\n\n"
            f"*{title}*\n\n"
            f"⚠️ No participants attempted the quiz."
        )
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        return

    lines = [
        "🏁 *QUIZ COMPLETE!*",
        f"*{title}* (Total Questions: {total_q})\n",
        "🏆 *FINAL LEADERBOARD:*\n"
    ]

    for r in rankings:
        lines.append(
            f"{r['medal']} *{r['name']}* — *{r['score']} pts*\n"
            f"   ✅ Correct: {r['correct']} | ❌ Wrong: {r['wrong']} | ⌛ Skipped: {r['skipped']}\n"
            f"   ⏱ Avg Time: {r['avg_time']}s\n"
        )

    lines.append(f"👥 Total Participants: {total_participants}")
    leaderboard_text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=chat_id,
        text=leaderboard_text,
        parse_mode=ParseMode.MARKDOWN
    )
