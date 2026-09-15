"""Application entrypoint supporting Webhook and Long-Polling modes."""

import sys
from app.config import settings
from app.database.connection import init_db
from app.bot.setup import create_bot_application, setup_bot_commands
from app.utils.logger import logger


async def post_init(application) -> None:
    """Post initialization hook: register commands and verify bot username."""
    await setup_bot_commands(application)
    bot_info = await application.bot.get_me()
    logger.info(f"Bot connected: @{bot_info.username} (ID: {bot_info.id})")


def main() -> None:
    """Main execution function."""
    logger.info(f"Starting NEET QuizBot in [{settings.ENVIRONMENT}] mode...")
    
    # Initialize DB tables
    init_db()

    # Build bot application
    application = create_bot_application()
    application.post_init = post_init

    # Run in Webhook or Polling mode
    if settings.WEBHOOK_URL:
        webhook_path = f"/webhook/{settings.BOT_TOKEN}"
        full_webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}{webhook_path}"
        logger.info(f"Starting in Webhook mode on port {settings.PORT}...")
        logger.info(f"Webhook URL configured: {settings.WEBHOOK_URL}...")

        application.run_webhook(
            listen="0.0.0.0",
            port=settings.PORT,
            url_path=webhook_path,
            webhook_url=full_webhook_url,
            drop_pending_updates=True
        )
    else:
        logger.info("Starting in Long-Polling mode (local development)...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "poll", "poll_answer", "callback_query"]
        )


if __name__ == "__main__":
    main()
