from folderbox.ui.theme import (
    DEFAULT_ACCENT_COLOR,
    build_stylesheet,
    normalize_accent_color,
    normalize_theme_mode,
)


def test_normalize_accent_color() -> None:
    assert normalize_accent_color("#8B5CF6") == "#8b5cf6"
    assert normalize_accent_color("invalid") == DEFAULT_ACCENT_COLOR


def test_normalize_theme_mode() -> None:
    assert normalize_theme_mode("dark") == "dark"
    assert normalize_theme_mode("unknown") == "light"


def test_dark_theme_uses_requested_accent() -> None:
    stylesheet = build_stylesheet(0.8, "#22c55e", "dark")

    assert "#22c55e" in stylesheet
    assert "background: rgba(24, 28, 36" in stylesheet
