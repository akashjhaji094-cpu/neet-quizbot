"""Branding and promotional configuration for NEET QuizBot."""

from typing import List
from telegram import InlineKeyboardButton

GLOBAL_PROMO_TEXT = ""

PROMO_SITE_URL = "https://neetverse.site"
PROMO_CHANNEL_URL = "https://t.me/neet_prepration2027_28"


def get_promo_keyboard_row() -> List[InlineKeyboardButton]:
    """Returns promo action buttons row for inline keyboards."""
    return [
        InlineKeyboardButton("🔥 Visit NEETVerse.site", url=PROMO_SITE_URL),
        InlineKeyboardButton("📲 Join Mentorship", url=PROMO_CHANNEL_URL)
    ]
