"""Branding and promotional configuration for NEET QuizBot."""

from typing import List
from telegram import InlineKeyboardButton

GLOBAL_PROMO_TEXT = (
    "🚀 *NEET 2027/28 Aspirants — Don’t Just Prepare, Prepare Smarter!*\n"
    "🔥 *NEETVerse.site* — Your AI-powered NEET preparation platform\n"
    "🧠 AI-Based CBT Tests\n"
    "📊 AI Analytics\n"
    "📚 4 Lakh+ Questions\n"
    "🎯 PYQs & Mock Tests\n"
    "👨‍🏫 FREE Mentorship\n"
    "💻 100% FREE to Start\n"
    "⚡ *Stop scrolling. Start preparing NOW!*\n"
    "👉 *Visit:* [neetverse.site](https://neetverse.site)\n"
    "📲 *Join FREE Mentorship:* [t.me/neet\\_prepration2027\\_28](https://t.me/neet_prepration2027_28)\n"
    "✨ *Your NEET journey starts here. 🚀*"
)

PROMO_SITE_URL = "https://neetverse.site"
PROMO_CHANNEL_URL = "https://t.me/neet_prepration2027_28"


def get_promo_keyboard_row() -> List[InlineKeyboardButton]:
    """Returns promo action buttons row for inline keyboards."""
    return [
        InlineKeyboardButton("🔥 Visit NEETVerse.site", url=PROMO_SITE_URL),
        InlineKeyboardButton("📲 Join Mentorship", url=PROMO_CHANNEL_URL)
    ]
