from folderbox.file_model import name_filter_pattern


def test_name_filter_pattern_wraps_plain_text() -> None:
    assert name_filter_pattern("report") == "*report*"


def test_name_filter_pattern_preserves_user_wildcards() -> None:
    assert name_filter_pattern("*.pdf") == "*.pdf"
    assert name_filter_pattern("image?.png") == "image?.png"


def test_name_filter_pattern_ignores_blank_text() -> None:
    assert name_filter_pattern("   ") is None
