from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager, DEFAULT_WINDOW_STATE
from folderbox.main_window import MainWindow
from folderbox.utils import path_exists


class WindowManager:
    def __init__(self, app: QApplication, config: ConfigManager) -> None:
        self.app = app
        self.config = config
        self.windows: list[MainWindow] = []
        self._last_snapshot: dict[str, Any] | None = None
        self.app.aboutToQuit.connect(self.save_window_states)

    def restore_windows(self) -> None:
        states = self._valid_saved_window_states() or [DEFAULT_WINDOW_STATE.copy()]
        for index, state in enumerate(states):
            self.create_window(initial_state=state, offset_index=index, show=True)

    def create_window(
        self,
        initial_state: dict[str, Any] | None = None,
        offset_index: int = 0,
        show: bool = True,
        ask_folder: bool = False,
    ) -> MainWindow:
        window = MainWindow(
            self.config,
            manager=self,
            initial_state=initial_state,
            instance_offset=offset_index,
        )
        self.windows.append(window)
        if show:
            window.show()
        if ask_folder:
            window.choose_folder()
        return window

    def open_new_window(self, source: MainWindow) -> None:
        base = source.snapshot_state()
        base["folder"] = ""
        base["x"] = int(base.get("x", 200)) + 36
        base["y"] = int(base.get("y", 200)) + 36
        self.create_window(
            initial_state=base,
            offset_index=len(self.windows),
            show=True,
            ask_folder=True,
        )
        self.save_window_states()

    def unregister_window(self, window: MainWindow) -> None:
        snapshot = window.snapshot_state()
        self._last_snapshot = snapshot
        if window in self.windows:
            self.windows.remove(window)
        self.save_window_states(fallback=snapshot)

    def save_window_states(self, fallback: dict[str, Any] | None = None) -> None:
        states = [window.snapshot_state() for window in self.windows if window.isVisible()]
        if not states and fallback:
            states = [fallback]
        elif not states and self._last_snapshot:
            states = [self._last_snapshot]

        self.config.set("windows", states)
        self.config.save()

    def _valid_saved_window_states(self) -> list[dict[str, Any]]:
        raw_states = self.config.get("windows", [])
        if not isinstance(raw_states, list):
            return []

        states: list[dict[str, Any]] = []
        for item in raw_states:
            if not isinstance(item, dict):
                continue
            folder = str(item.get("folder", "") or "")
            if folder and not path_exists(folder):
                folder = ""
            states.append(
                {
                    "folder": folder,
                    "x": int(item.get("x", DEFAULT_WINDOW_STATE["x"]) or DEFAULT_WINDOW_STATE["x"]),
                    "y": int(item.get("y", DEFAULT_WINDOW_STATE["y"]) or DEFAULT_WINDOW_STATE["y"]),
                    "width": int(item.get("width", DEFAULT_WINDOW_STATE["width"]) or DEFAULT_WINDOW_STATE["width"]),
                    "height": int(item.get("height", DEFAULT_WINDOW_STATE["height"]) or DEFAULT_WINDOW_STATE["height"]),
                    "always_on_top": bool(item.get("always_on_top", DEFAULT_WINDOW_STATE["always_on_top"])),
                    "background_opacity": float(
                        item.get("background_opacity", DEFAULT_WINDOW_STATE["background_opacity"])
                    ),
                    "view_mode": str(
                        item.get("view_mode", DEFAULT_WINDOW_STATE["view_mode"])
                        or DEFAULT_WINDOW_STATE["view_mode"]
                    ),
                }
            )
        return states
