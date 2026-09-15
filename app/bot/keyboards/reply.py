"""Reply keyboards including native poll request button."""

from telegram import KeyboardButton, KeyboardButtonPollType, Poll, ReplyKeyboardMarkup, ReplyKeyboardRemove
from app.utils.localization import t


def get_create_question_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Returns reply keyboard with native poll request button.
    Crucial: Uses KeyboardButtonPollType(type=Poll.QUIZ).
    """
    button_text = t("btn_create_question", lang)
    keyboard = [
        [
            KeyboardButton(
                text=button_text,
                request_poll=KeyboardButtonPollType(type=Poll.QUIZ)
            )
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True
    )


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """Removes active custom reply keyboard."""
    return ReplyKeyboardRemove()
