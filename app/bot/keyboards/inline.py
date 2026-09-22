"""Inline keyboards for menus, settings, attempts, and results."""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.localization import t


from app.config import settings


def get_start_keyboard(bot_username: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    """Home /start inline menu matching the requested UI layout."""
    clean_bot = (bot_username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")
    owner_username = (settings.OWNER_USERNAME or "zx_era").lstrip("@")
    owner_link = f"https://t.me/{owner_username}"
    support_link = settings.SUPPORT_URL or "https://t.me/SuperQuizUpdates"

    keyboard = [
        [InlineKeyboardButton("Add this bot to your group", url=f"https://t.me/{clean_bot}?startgroup=true")],
        [InlineKeyboardButton("Create New Quiz", callback_data="cmd:newquiz")],
        [
            InlineKeyboardButton("Owner", url=owner_link),
            InlineKeyboardButton("Help", callback_data="cmd:help")
        ],
        [InlineKeyboardButton("Support", url=support_link)]
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
    """Marking scheme selection keyboard (+4/-1, +1/-0.33, +1/0)."""
    keyboard = [
        [InlineKeyboardButton("🎯 NEET Marking (+4 / -1)", callback_data="marking:4:-1")],
        [InlineKeyboardButton("🏥 NORCET Marking (+1 / -0.33)", callback_data="marking:1:-0.33")],
        [InlineKeyboardButton("✅ Simple Marking (+1 / 0)", callback_data="marking:1:0")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_intro_keyboard(quiz_code: str, bot_username: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard shown before starting a quiz attempt with option to start in group."""
    from app.utils.branding import get_promo_keyboard_row
    clean_bot = bot_username.lstrip("@") if bot_username else "akaxxh_bot"
    group_url = f"https://t.me/{clean_bot}?startgroup=quiz_{quiz_code}"
    keyboard = [
        [InlineKeyboardButton(f"▶️ {t('btn_start_quiz', lang)}", callback_data=f"start_attempt:{quiz_code}")],
        [InlineKeyboardButton("Start quiz in group", url=group_url)],
        get_promo_keyboard_row()
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_created_keyboard(quiz_code: str, bot_username: str = "") -> InlineKeyboardMarkup:
    """Keyboard shown immediately after quiz creation matching Image 1."""
    clean_bot = (bot_username or settings.BOT_USERNAME or "akaxxh_bot").lstrip("@")
    group_url = f"https://t.me/{clean_bot}?startgroup=quiz_{quiz_code}"
    keyboard = [
        [InlineKeyboardButton("Start this quiz", callback_data=f"start_attempt:{quiz_code}")],
        [InlineKeyboardButton("Start quiz in group", url=group_url)],
        [InlineKeyboardButton("Share quiz", switch_inline_query=f"quiz:{quiz_code}")],
        [InlineKeyboardButton("Edit quiz", callback_data=f"edit_quiz:{quiz_code}")],
        [InlineKeyboardButton("Quiz stats", callback_data=f"stats:{quiz_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_quiz_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Dashboard keyboard for editing an existing quiz."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Edit Title", callback_data=f"edit_title:{quiz_code}"),
            InlineKeyboardButton("📄 Edit Description", callback_data=f"edit_desc:{quiz_code}")
        ],
        [
            InlineKeyboardButton("⏱ Edit Timer", callback_data=f"edit_timer:{quiz_code}"),
            InlineKeyboardButton("🔀 Edit Shuffle", callback_data=f"edit_shuffle:{quiz_code}")
        ],
        [
            InlineKeyboardButton("⚖️ Edit Marking Scheme", callback_data=f"edit_marking:{quiz_code}")
        ],
        [
            InlineKeyboardButton("🗑 Delete Quiz", callback_data=f"del_quiz:{quiz_code}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Quiz", callback_data=f"back_to_quiz:{quiz_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_timer_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Timer selection keyboard when editing a quiz."""
    keyboard = [
        [
            InlineKeyboardButton("10 seconds", callback_data=f"ed_tm:{quiz_code}:10"),
            InlineKeyboardButton("15 seconds", callback_data=f"ed_tm:{quiz_code}:15"),
            InlineKeyboardButton("20 seconds", callback_data=f"ed_tm:{quiz_code}:20")
        ],
        [
            InlineKeyboardButton("30 seconds", callback_data=f"ed_tm:{quiz_code}:30"),
            InlineKeyboardButton("45 seconds", callback_data=f"ed_tm:{quiz_code}:45"),
            InlineKeyboardButton("1 min", callback_data=f"ed_tm:{quiz_code}:60")
        ],
        [
            InlineKeyboardButton("1.5 min", callback_data=f"ed_tm:{quiz_code}:90"),
            InlineKeyboardButton("2 min", callback_data=f"ed_tm:{quiz_code}:120"),
            InlineKeyboardButton("3 min", callback_data=f"ed_tm:{quiz_code}:180")
        ],
        [
            InlineKeyboardButton("5 min", callback_data=f"ed_tm:{quiz_code}:300"),
            InlineKeyboardButton("No Timer", callback_data=f"ed_tm:{quiz_code}:0")
        ],
        [
            InlineKeyboardButton("🔙 Back to Edit Menu", callback_data=f"edit_quiz:{quiz_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_shuffle_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Shuffle selection keyboard when editing a quiz."""
    keyboard = [
        [InlineKeyboardButton("🔀 Shuffle All", callback_data=f"ed_sh:{quiz_code}:all")],
        [InlineKeyboardButton("❓ Shuffle Questions", callback_data=f"ed_sh:{quiz_code}:questions")],
        [InlineKeyboardButton("🔤 Shuffle Options", callback_data=f"ed_sh:{quiz_code}:options")],
        [InlineKeyboardButton("➡️ Don't Shuffle", callback_data=f"ed_sh:{quiz_code}:none")],
        [InlineKeyboardButton("🔙 Back to Edit Menu", callback_data=f"edit_quiz:{quiz_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_marking_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Marking selection keyboard when editing a quiz."""
    keyboard = [
        [InlineKeyboardButton("🎯 NEET Marking (+4 / -1)", callback_data=f"ed_mk:{quiz_code}:4:-1")],
        [InlineKeyboardButton("🏥 NORCET Marking (+1 / -0.33)", callback_data=f"ed_mk:{quiz_code}:1:-0.33")],
        [InlineKeyboardButton("✅ Simple Marking (+1 / 0)", callback_data=f"ed_mk:{quiz_code}:1:0")],
        [InlineKeyboardButton("🔙 Back to Edit Menu", callback_data=f"edit_quiz:{quiz_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_delete_confirm_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard before deleting a quiz."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"del_confirm:{quiz_code}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"edit_quiz:{quiz_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for /support command."""
    keyboard = [
        [InlineKeyboardButton("📢 Join Support Channel", url="https://t.me/SuperQuizUpdates")],
        [InlineKeyboardButton("💬 Contact Support", url="https://t.me/zx_era")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_group_ready_keyboard(quiz_code: str, ready_count: int = 0) -> InlineKeyboardMarkup:
    """Ready button for group quiz starting flow with live participant count."""
    from app.utils.branding import get_promo_keyboard_row
    label = f"✋ I'm ready! ({ready_count})" if ready_count > 0 else "✋ I'm ready!"
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"grp_ready:{quiz_code}")],
        get_promo_keyboard_row()
    ]
    return InlineKeyboardMarkup(keyboard)


def get_group_intro_keyboard(quiz_code: str) -> InlineKeyboardMarkup:
    """Keyboard shown in group before launching the quiz."""
    return get_group_ready_keyboard(quiz_code, ready_count=0)


def get_quiz_result_keyboard(quiz_code: str, bot_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard shown upon quiz completion."""
    from app.utils.branding import get_promo_keyboard_row
    clean_bot = bot_username.lstrip("@")
    group_url = f"https://t.me/{clean_bot}?startgroup=quiz_{quiz_code}"

    keyboard = [
        [InlineKeyboardButton(f"🔄 {t('btn_try_again', lang)}", callback_data=f"start_attempt:{quiz_code}")],
        [InlineKeyboardButton("Share quiz", switch_inline_query=f"quiz:{quiz_code}")],
        [InlineKeyboardButton("Start quiz in group", url=group_url)],
        get_promo_keyboard_row(),
        [InlineKeyboardButton(f"🏠 {t('btn_back', lang)}", callback_data="cmd:start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_item_keyboard(quiz_code: str, bot_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for an individual quiz in the /quizzes list."""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Start", callback_data=f"start_attempt:{quiz_code}"),
            InlineKeyboardButton("Share quiz", switch_inline_query=f"quiz:{quiz_code}"),
            InlineKeyboardButton("📊 Stats", callback_data=f"stats:{quiz_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
