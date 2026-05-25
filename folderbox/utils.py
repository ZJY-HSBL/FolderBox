from __future__ import annotations

import os
import platform
from pathlib import Path

WINDOWS_INVALID_FILENAME_CHARS = set('\\/:*?"<>|')


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def path_exists(path: str | Path | None) -> bool:
    if not path:
        return False
    try:
        return Path(path).exists()
    except (OSError, ValueError):
        return False


def is_valid_windows_filename(name: str) -> bool:
    if not name or not name.strip():
        return False
    if name in {".", ".."}:
        return False
    if any(char in WINDOWS_INVALID_FILENAME_CHARS for char in name):
        return False
    return True


def shorten_path(path: str | Path, max_chars: int = 64) -> str:
    text = str(path)
    if len(text) <= max_chars:
        return text

    path_obj = Path(text)
    drive = path_obj.drive
    name = path_obj.name
    prefix = drive + os.sep if drive else ""
    remaining = max_chars - len(prefix) - len(name) - 5
    if remaining <= 0:
        return f"{prefix}...{name}" if prefix else f"...{name[-max_chars + 3:]}"

    middle = text[len(prefix) : -len(name)] if name else text[len(prefix) :]
    return f"{prefix}{middle[:remaining]}...{os.sep}{name}"


def format_file_size(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def format_exception(exc: BaseException) -> str:
    message = str(exc).strip()
    return message if message else exc.__class__.__name__
