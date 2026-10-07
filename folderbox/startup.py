from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from folderbox.utils import is_windows

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "FolderBox"


class StartupError(Exception):
    """Raised when the Windows startup registration cannot be changed."""


def build_startup_command(executable: str | Path, frozen: bool) -> str:
    target = Path(executable)
    if frozen:
        return subprocess.list2cmdline([str(target)])

    if target.name.lower() == "python.exe":
        pythonw = target.with_name("pythonw.exe")
        if pythonw.exists():
            target = pythonw
    return subprocess.list2cmdline([str(target), "-m", "folderbox"])


def startup_command() -> str:
    return build_startup_command(sys.executable, bool(getattr(sys, "frozen", False)))


def is_startup_enabled() -> bool:
    if not is_windows():
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return str(value).strip() == startup_command().strip()


def set_startup_enabled(enabled: bool) -> None:
    if not is_windows():
        raise StartupError("开机启动仅支持 Windows。")

    import winreg

    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    VALUE_NAME,
                    0,
                    winreg.REG_SZ,
                    startup_command(),
                )
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
    except OSError as exc:
        raise StartupError(f"无法修改 Windows 开机启动设置：{exc}") from exc
