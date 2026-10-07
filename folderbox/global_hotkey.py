from __future__ import annotations

import ctypes
from collections.abc import Callable

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

from folderbox.utils import is_windows

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 0x4642
HOTKEY_VK = ord("B")


class HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, callback: Callable[[], None]) -> None:
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if not is_windows():
            return False, 0

        from ctypes import wintypes

        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY and int(msg.wParam) == HOTKEY_ID:
            self.callback()
            return True, 0
        return False, 0


class GlobalHotkeyController:
    def __init__(self, app: QApplication, callback: Callable[[], None]) -> None:
        self.app = app
        self.filter = HotkeyEventFilter(callback)
        self.registered = False
        self.app.installNativeEventFilter(self.filter)
        self.app.aboutToQuit.connect(self.unregister)

    @staticmethod
    def description() -> str:
        return "Ctrl+Alt+B"

    def register(self) -> bool:
        if not is_windows():
            return False

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        modifiers = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
        self.registered = bool(
            user32.RegisterHotKey(None, HOTKEY_ID, modifiers, HOTKEY_VK)
        )
        return self.registered

    def unregister(self) -> None:
        if not self.registered or not is_windows():
            return

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.UnregisterHotKey(None, HOTKEY_ID)
        self.registered = False
