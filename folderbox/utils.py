from __future__ import annotations

import platform
from pathlib import Path

WINDOWS_INVALID_FILENAME_CHARS = set('\\/:*?"<>|')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


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
    if name in {".", ".."} or len(name) > 255:
        return False
    if name.endswith((" ", ".")):
        return False
    if any(ord(char) < 32 or char in WINDOWS_INVALID_FILENAME_CHARS for char in name):
        return False
    device_name = name.split(".", 1)[0].upper()
    return device_name not in WINDOWS_RESERVED_NAMES


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
