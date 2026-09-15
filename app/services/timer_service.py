"""Server-side question countdown timer service using python-telegram-bot JobQueue."""

from typing import Any, Dict
from telegram.ext import ContextTypes
from app.utils.logger import logger


class TimerService:
    """Manages active question timers to ensure server-side timeouts."""

    @staticmethod
    def schedule_question_timeout(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        attempt_id: int,
        attempt_question_id: int,
        timer_seconds: int,
        callback_coroutine: Any
    ) -> None:
        """Schedule a job to fire when the question timer expires."""
        if not context.job_queue:
            logger.warning("JobQueue is not initialized; timeout scheduling skipped.")
            return

        job_name = f"timeout_{attempt_id}_{attempt_question_id}"
        
        # Remove any previous job with same name
        existing_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in existing_jobs:
            job.schedule_removal()

        context.job_queue.run_once(
            callback=callback_coroutine,
            when=timer_seconds,
            chat_id=chat_id,
            name=job_name,
            data={
                "chat_id": chat_id,
                "attempt_id": attempt_id,
                "attempt_question_id": attempt_question_id
            }
        )
        logger.info(f"Scheduled timer job {job_name} for {timer_seconds} seconds.")

    @staticmethod
    def cancel_question_timeout(
        context: ContextTypes.DEFAULT_TYPE,
        attempt_id: int,
        attempt_question_id: int
    ) -> None:
        """Cancel a pending question timeout job when the user answers before timeout."""
        if not context.job_queue:
            return

        job_name = f"timeout_{attempt_id}_{attempt_question_id}"
        existing_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in existing_jobs:
            job.schedule_removal()
            logger.info(f"Cancelled timer job {job_name}.")
