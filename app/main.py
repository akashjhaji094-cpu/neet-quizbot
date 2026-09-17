import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from app.config import settings
from app.database.connection import init_db
from app.bot.setup import create_bot_application, setup_bot_commands
from app.utils.logger import logger


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","app":"NEET QuizBot"}')

    def log_message(self, format, *args):
        pass


def start_health_server(port: int) -> None:
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Health check HTTP server listening on port {port} (satisfies Heroku web dyno port binding).")
    except Exception as e:
        logger.warning(f"Could not bind health check HTTP server on port {port}: {e}")


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
        # If running on Heroku / Render as a 'web' dyno, bind to $PORT to satisfy boot check
        assigned_port = int(os.environ.get("PORT", 0))
        if assigned_port > 0:
            start_health_server(assigned_port)

        logger.info("Starting in Long-Polling mode...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "poll", "poll_answer", "callback_query", "inline_query"]
        )


if __name__ == "__main__":
    main()
