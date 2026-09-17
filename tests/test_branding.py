"""Unit tests for global branding and promotional watermark configuration."""

from app.utils.branding import GLOBAL_PROMO_TEXT, get_promo_keyboard_row, PROMO_SITE_URL, PROMO_CHANNEL_URL


def test_branding_content():
    """Verify promo text contains required links, channels, and highlights."""
    assert "neetverse.site" in GLOBAL_PROMO_TEXT
    assert "t.me/neet" in GLOBAL_PROMO_TEXT
    assert "NEET 2027/28" in GLOBAL_PROMO_TEXT
    assert "AI-Based CBT Tests" in GLOBAL_PROMO_TEXT


def test_branding_keyboards():
    """Verify promo buttons row creates valid inline URL buttons."""
    row = get_promo_keyboard_row()
    assert len(row) == 2
    assert row[0].url == PROMO_SITE_URL
    assert row[1].url == PROMO_CHANNEL_URL
