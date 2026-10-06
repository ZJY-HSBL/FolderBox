from folderbox.utils import is_valid_windows_filename


def test_accepts_normal_windows_filename() -> None:
    assert is_valid_windows_filename("paper-results_v2.txt")


def test_rejects_reserved_windows_device_names() -> None:
    for name in ("CON", "con.txt", "PRN.md", "COM1", "LPT9.log", "NUL"):
        assert not is_valid_windows_filename(name)


def test_rejects_invalid_or_trailing_characters() -> None:
    for name in ("bad:name.txt", "bad?.txt", "folder.", "folder ", "."):
        assert not is_valid_windows_filename(name)
