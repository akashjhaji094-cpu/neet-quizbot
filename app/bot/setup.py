"""Bot application builder and handler setup."""

from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    PollAnswerHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters
)
from app.config import settings
from app.bot.handlers import (
    start_command,
    newquiz_command,
    quizzes_command,
    undo_command,
    done_command,
    cancel_command,
    stop_command,
    help_command,
    support_command,
    lang_command,
    stats_command,
    handle_creation_text,
    handle_skip_command,
    handle_prequestion_media,
    handle_native_poll_received,
    handle_quiz_share_command,
    handle_poll_answer,
    handle_callback_query,
    handle_inline_query
)
from app.utils.logger import logger


async def setup_bot_commands(application: Application) -> None:
    """Configure official Telegram Bot command menu via setMyCommands."""
    commands = [
        BotCommand("start", "Start bot and learn how to use it"),
        BotCommand("newquiz", "Create a new quiz"),
        BotCommand("quizzes", "Show your quizzes"),
        BotCommand("undo", "Undo last question"),
        BotCommand("done", "Finish quiz creation"),
        BotCommand("cancel", "Cancel current quiz creation"),
        BotCommand("skip", "Skip quiz description"),
        BotCommand("stop", "Stop active session"),
        BotCommand("lang", "Change language"),
        BotCommand("help", "About this bot and scoring rules"),
        BotCommand("support", "Support channel and assistance"),
        BotCommand("stats", "View your creator statistics")
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot command menu configured successfully.")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")


def create_bot_application() -> Application:
    """Assemble and configure the python-telegram-bot Application."""
    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    # 1. Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("newquiz", newquiz_command))
    app.add_handler(CommandHandler("quizzes", quizzes_command))
    app.add_handler(CommandHandler("myquizzes", quizzes_command))
    app.add_handler(CommandHandler("quiz", handle_quiz_share_command))
    app.add_handler(CommandHandler("skip", handle_skip_command))
    app.add_handler(CommandHandler("undo", undo_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # 2. Native poll reception handler (creator sends the completed quiz poll)
    app.add_handler(MessageHandler(filters.POLL, handle_native_poll_received))

    # 3. Pre-question media handler (photo, video, animation, document)
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.ANIMATION | filters.Document.ALL,
            handle_prequestion_media
        )
    )

    # 4. Text handler for creation states (title, description)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_creation_text))

    # 5. Participant poll answer update handler
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    # 6. Inline keyboard callback handler
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # 7. Inline query handler for rich quiz sharing (@bot quiz:CODE)
    app.add_handler(InlineQueryHandler(handle_inline_query))

    return app
