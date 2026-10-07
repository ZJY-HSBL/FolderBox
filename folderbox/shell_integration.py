from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from folderbox.utils import is_windows

MENU_TEXT = "Open in FolderBox"
DIRECTORY_KEY = r"Software\Classes\Directory\shell\FolderBox"
BACKGROUND_KEY = r"Software\Classes\Directory\Background\shell\FolderBox"


class ShellIntegrationError(Exception):
    """Raised when Explorer context-menu registration cannot be changed."""


def _runtime_command_prefix(executable: str | Path, frozen: bool) -> str:
    target = Path(executable)
    if frozen:
        return subprocess.list2cmdline([str(target)])

    if target.name.lower() == "python.exe":
        pythonw = target.with_name("pythonw.exe")
        if pythonw.exists():
            target = pythonw
    return f"{subprocess.list2cmdline([str(target)])} -m folderbox"


def build_shell_command(
    executable: str | Path,
    frozen: bool,
    placeholder: str,
) -> str:
    prefix = _runtime_command_prefix(executable, frozen)
    return f'{prefix} --folder "{placeholder}"'


def shell_commands() -> dict[str, str]:
    frozen = bool(getattr(sys, "frozen", False))
    return {
        DIRECTORY_KEY: build_shell_command(sys.executable, frozen, "%1"),
        BACKGROUND_KEY: build_shell_command(sys.executable, frozen, "%V"),
    }


def is_shell_integration_enabled() -> bool:
    if not is_windows():
        return False

    import winreg

    for root_path, expected_command in shell_commands().items():
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                root_path + r"\command",
            ) as key:
                command, _ = winreg.QueryValueEx(key, "")
        except OSError:
            return False
        if str(command).strip() != expected_command.strip():
            return False
    return True


def set_shell_integration_enabled(enabled: bool) -> None:
    if not is_windows():
        raise ShellIntegrationError("资源管理器右键集成仅支持 Windows。")

    import winreg

    try:
        if enabled:
            frozen = bool(getattr(sys, "frozen", False))
            for root_path, command in shell_commands().items():
                with winreg.CreateKeyEx(
                    winreg.HKEY_CURRENT_USER,
                    root_path,
                    0,
                    winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_TEXT)
                    if frozen:
                        winreg.SetValueEx(
                            key,
                            "Icon",
                            0,
                            winreg.REG_SZ,
                            str(Path(sys.executable)),
                        )

                with winreg.CreateKeyEx(
                    winreg.HKEY_CURRENT_USER,
                    root_path + r"\command",
                    0,
                    winreg.KEY_SET_VALUE,
                ) as command_key:
                    winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command)
        else:
            for root_path in (DIRECTORY_KEY, BACKGROUND_KEY):
                _delete_registry_tree(winreg, root_path)
    except OSError as exc:
        raise ShellIntegrationError(f"无法修改资源管理器右键菜单：{exc}") from exc


def _delete_registry_tree(winreg, path: str) -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            children: list[str] = []
            index = 0
            while True:
                try:
                    children.append(winreg.EnumKey(key, index))
                    index += 1
                except OSError:
                    break
    except FileNotFoundError:
        return

    for child in children:
        _delete_registry_tree(winreg, path + "\\" + child)

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass
