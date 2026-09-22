"""Reply keyboards including native poll request button and step-by-step quiz settings."""

from telegram import KeyboardButton, KeyboardButtonPollType, Poll, ReplyKeyboardMarkup, ReplyKeyboardRemove
from app.utils.localization import t


def get_create_question_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Returns reply keyboard with native poll request button and flow controls.
    is_persistent=False allows user to dismiss or switch to normal text typing.
    """
    button_text = t("btn_create_question", lang)
    keyboard = [
        [
            KeyboardButton(
                text=f"➕ {button_text}",
                request_poll=KeyboardButtonPollType(type=Poll.QUIZ)
            )
        ],
        [
            KeyboardButton("🏁 Done"),
            KeyboardButton("↩️ Undo"),
            KeyboardButton("❌ Cancel")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=False
    )


def get_timer_reply_keyboard() -> ReplyKeyboardMarkup:
    """Bottom reply keyboard for selecting question timer limit."""
    keyboard = [
        [KeyboardButton("10 sec"), KeyboardButton("15 sec"), KeyboardButton("30 sec")],
        [KeyboardButton("45 sec"), KeyboardButton("1 min"), KeyboardButton("2 min")],
        [KeyboardButton("3 min"), KeyboardButton("5 min"), KeyboardButton("No Timer")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=False
    )


def get_shuffle_reply_keyboard() -> ReplyKeyboardMarkup:
    """Bottom reply keyboard for selecting shuffle options."""
    keyboard = [
        [KeyboardButton("🔀 Shuffle All"), KeyboardButton("➡️ No Shuffle")],
        [KeyboardButton("❓ Shuffle Questions"), KeyboardButton("🔤 Shuffle Options")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=False
    )


def get_marking_reply_keyboard() -> ReplyKeyboardMarkup:
    """Bottom reply keyboard for selecting marking scheme."""
    keyboard = [
        [KeyboardButton("🎯 NEET Marking (+4 / -1)")],
        [KeyboardButton("🏥 NORCET Marking (+1 / -0.33)")],
        [KeyboardButton("✅ Simple Marking (+1 / 0)")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        is_persistent=False
    )


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """Removes active custom reply keyboard, restoring regular chat keyboard."""
    return ReplyKeyboardRemove()
