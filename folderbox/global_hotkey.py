from __future__ import annotations

import ctypes
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

from folderbox.utils import is_windows

if TYPE_CHECKING:
    from folderbox.window_manager import WindowManager


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000

TOGGLE_HOTKEY_ID = 0x4642
TOGGLE_HOTKEY_VK = ord("B")
WORKSPACE_HOTKEY_BASE_ID = 0x4700


def workspace_hotkey_id(slot: int) -> int:
    return WORKSPACE_HOTKEY_BASE_ID + slot


def workspace_hotkey_vk(slot: int) -> int:
    if slot not in range(1, 10):
        raise ValueError("Workspace hotkey slot must be between 1 and 9.")
    return ord(str(slot))


class HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, callbacks: dict[int, Callable[[], None]]) -> None:
        super().__init__()
        self.callbacks = callbacks

    def nativeEventFilter(self, event_type, message):
        if not is_windows():
            return False, 0

        from ctypes import wintypes

        msg = wintypes.MSG.from_address(int(message))
        if msg.message != WM_HOTKEY:
            return False, 0

        callback = self.callbacks.get(int(msg.wParam))
        if callback is None:
            return False, 0

        callback()
        return True, 0


class GlobalHotkeyController:
    def __init__(self, app: QApplication, manager: WindowManager) -> None:
        self.app = app
        self.manager = manager
        self.callbacks: dict[int, Callable[[], None]] = {}
        self.registered_ids: set[int] = set()
        self.workspace_registered_slots: set[int] = set()
        self.filter = HotkeyEventFilter(self.callbacks)
        self.app.installNativeEventFilter(self.filter)
        self.app.aboutToQuit.connect(self.unregister)
        self.manager.add_workspace_change_listener(self.refresh_workspace_hotkeys)

    @staticmethod
    def description() -> str:
        return "Ctrl+Alt+B"

    @staticmethod
    def workspace_description(slot: int) -> str:
        workspace_hotkey_vk(slot)
        return f"Ctrl+Alt+{slot}"

    def register(self) -> bool:
        if not is_windows():
            return False

        toggle_registered = self._register_hotkey(
            TOGGLE_HOTKEY_ID,
            TOGGLE_HOTKEY_VK,
            self.manager.toggle_all,
        )
        self.refresh_workspace_hotkeys()
        return toggle_registered

    def refresh_workspace_hotkeys(self) -> dict[int, bool]:
        for slot in tuple(self.workspace_registered_slots):
            self._unregister_hotkey(workspace_hotkey_id(slot))
        self.workspace_registered_slots.clear()

        results: dict[int, bool] = {}
        if not is_windows():
            return results

        for slot in sorted(self.manager.workspace_hotkey_bindings()):
            registered = self._register_hotkey(
                workspace_hotkey_id(slot),
                workspace_hotkey_vk(slot),
                lambda value=slot: self.manager.load_workspace_by_hotkey(value),
            )
            results[slot] = registered
            if registered:
                self.workspace_registered_slots.add(slot)
        return results

    def _register_hotkey(
        self,
        hotkey_id: int,
        virtual_key: int,
        callback: Callable[[], None],
    ) -> bool:
        if not is_windows():
            return False

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        modifiers = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
        registered = bool(
            user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key)
        )
        if registered:
            self.registered_ids.add(hotkey_id)
            self.callbacks[hotkey_id] = callback
        return registered

    def _unregister_hotkey(self, hotkey_id: int) -> None:
        self.callbacks.pop(hotkey_id, None)
        if hotkey_id not in self.registered_ids:
            return

        if is_windows():
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            user32.UnregisterHotKey(None, hotkey_id)
        self.registered_ids.discard(hotkey_id)

    def unregister(self) -> None:
        for hotkey_id in tuple(self.registered_ids):
            self._unregister_hotkey(hotkey_id)
        self.workspace_registered_slots.clear()
