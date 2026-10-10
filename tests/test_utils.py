from folderbox.utils import is_valid_windows_filename


def test_accepts_normal_windows_filename() -> None:
    assert is_valid_windows_filename("paper-results_v2.txt")


def test_rejects_reserved_windows_device_names() -> None:
    for name in ("CON", "con.txt", "PRN.md", "COM1", "LPT9.log", "NUL"):
        assert not is_valid_windows_filename(name)


def test_rejects_invalid_or_trailing_characters() -> None:
    for name in ("bad:name.txt", "bad?.txt", "folder.", "folder ", "."):
        assert not is_valid_windows_filename(name)


def test_rejects_superscript_windows_device_names() -> None:
    # Windows reserves COM¹–COM³ and LPT¹–LPT³ (with or without extensions).
    for prefix in ("COM", "LPT"):
        for digit in "¹²³":
            for name in (f"{prefix}{digit}", f"{prefix.lower()}{digit}.txt"):
                assert not is_valid_windows_filename(name)


def test_accepts_nonreserved_unicode_filenames() -> None:
    for name in ("报告².txt", "COM⁴.txt", "LPT⁴", "结果-2026.docx"):
        assert is_valid_windows_filename(name)
