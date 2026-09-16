"""Inline keyboards for menus, settings, attempts, and results."""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.localization import t


from app.config import settings


def get_start_keyboard(bot_username: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    """Home /start inline menu matching the requested UI layout."""
    clean_bot = (bot_username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")
    owner_link = f"https://t.me/{settings.OWNER_USERNAME.lstrip('@')}" if settings.OWNER_USERNAME else f"https://t.me/{clean_bot}"
    support_link = settings.SUPPORT_URL or f"https://t.me/{clean_bot}"

    keyboard = [
        [InlineKeyboardButton("➕ Add this bot to your group", url=f"https://t.me/{clean_bot}?startgroup=true")],
        [InlineKeyboardButton("➕ Create New Quiz", callback_data="cmd:newquiz")],
        [
            InlineKeyboardButton("Owner ↗️", url=owner_link),
            InlineKeyboardButton("Help ↗️", callback_data="cmd:help")
        ],
        [InlineKeyboardButton("Support ↗️", url=support_link)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_timer_keyboard() -> InlineKeyboardMarkup:
    """Timer selection keyboard per question with 45s and minute formatting."""
    keyboard = [
        [
            InlineKeyboardButton("10 seconds", callback_data="timer:10"),
            InlineKeyboardButton("15 seconds", callback_data="timer:15"),
            InlineKeyboardButton("20 seconds", callback_data="timer:20")
        ],
        [
            InlineKeyboardButton("30 seconds", callback_data="timer:30"),
            InlineKeyboardButton("45 seconds", callback_data="timer:45"),
            InlineKeyboardButton("1 min", callback_data="timer:60")
        ],
        [
            InlineKeyboardButton("1.5 min", callback_data="timer:90"),
            InlineKeyboardButton("2 min", callback_data="timer:120"),
            InlineKeyboardButton("3 min", callback_data="timer:180")
        ],
        [
            InlineKeyboardButton("5 min", callback_data="timer:300"),
            InlineKeyboardButton("No Timer", callback_data="timer:0")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_shuffle_keyboard() -> InlineKeyboardMarkup:
    """Shuffle selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔀 Shuffle All", callback_data="shuffle:all")],
        [InlineKeyboardButton("❓ Shuffle Questions", callback_data="shuffle:questions")],
        [InlineKeyboardButton("🔤 Shuffle Options", callback_data="shuffle:options")],
        [InlineKeyboardButton("➡️ Don't Shuffle", callback_data="shuffle:none")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_marking_keyboard() -> InlineKeyboardMarkup:
    """Marking scheme selection keyboard (+4/-1, +1/-1, +1/0)."""
    keyboard = [
        [InlineKeyboardButton("🎯 NEET Marking (+4 / -1)", callback_data="marking:4:-1")],
        [InlineKeyboardButton("📝 General Marking (+1 / -1)", callback_data="marking:1:-1")],
        [InlineKeyboardButton("✅ Simple Marking (+1 / 0)", callback_data="marking:1:0")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_intro_keyboard(quiz_code: str, bot_username: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard shown before starting a quiz attempt with option to start in group."""
    clean_bot = bot_username.lstrip("@") if bot_username else "akaxxh_bot"
    group_url = f"https://t.me/{clean_bot}?startgroup=quiz_{quiz_code}"
    keyboard = [
        [InlineKeyboardButton(f"▶️ {t('btn_start_quiz', lang)}", callback_data=f"start_attempt:{quiz_code}")],
        [InlineKeyboardButton(f"👥 {t('btn_share_group', lang)}", url=group_url)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_group_intro_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Keyboard shown in group before launching the quiz."""
    keyboard = [
        [InlineKeyboardButton("▶️ Start Quiz Now", callback_data=f"start_grp:{quiz_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_result_keyboard(quiz_code: str, bot_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard shown upon quiz completion."""
    clean_bot = bot_username.lstrip("@")
    deep_link = f"https://t.me/{clean_bot}?start=quiz_{quiz_code}"
    share_url = f"https://t.me/share/url?url={deep_link}&text=Can%20you%20beat%20my%20score%20on%20this%20NEET%20Quiz?"
    group_url = f"https://t.me/{clean_bot}?startgroup=quiz_{quiz_code}"

    keyboard = [
        [InlineKeyboardButton(f"🔄 {t('btn_try_again', lang)}", callback_data=f"start_attempt:{quiz_code}")],
        [InlineKeyboardButton(f"📤 {t('btn_share_quiz', lang)}", url=share_url)],
        [InlineKeyboardButton(f"👥 {t('btn_share_group', lang)}", url=group_url)],
        [InlineKeyboardButton(f"🏠 {t('btn_back', lang)}", callback_data="cmd:start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_item_keyboard(quiz_code: str, bot_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for an individual quiz in the /quizzes list."""
    clean_bot = bot_username.lstrip("@")
    deep_link = f"https://t.me/{clean_bot}?start=quiz_{quiz_code}"
    share_url = f"https://t.me/share/url?url={deep_link}&text=Try%20this%20NEET%20Quiz!"

    keyboard = [
        [
            InlineKeyboardButton("▶️ Start", callback_data=f"start_attempt:{quiz_code}"),
            InlineKeyboardButton("📤 Share", url=share_url),
            InlineKeyboardButton("📊 Stats", callback_data=f"stats:{quiz_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
