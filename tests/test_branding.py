"""Unit tests for global branding and promotional watermark configuration."""

from app.utils.branding import GLOBAL_PROMO_TEXT, get_promo_keyboard_row, PROMO_SITE_URL, PROMO_CHANNEL_URL


def test_branding_content():
    """Verify promo text in message cards is disabled so messages stay clean."""
    assert GLOBAL_PROMO_TEXT == ""
    assert "neetverse.site" in PROMO_SITE_URL
    assert "t.me/neet" in PROMO_CHANNEL_URL


def test_branding_keyboards():
    """Verify promo buttons row creates valid inline URL buttons."""
    row = get_promo_keyboard_row()
    assert len(row) == 2
    assert row[0].url == PROMO_SITE_URL
    assert row[1].url == PROMO_CHANNEL_URL
