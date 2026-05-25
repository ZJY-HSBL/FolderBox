from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from folderbox import __app_name__
from folderbox.config_manager import ConfigManager
from folderbox.main_window import MainWindow
from folderbox.utils import path_exists


def asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "assets" / name
    return Path(__file__).resolve().parent.parent / "assets" / name


class WindowManager:
    def __init__(self, app: QApplication, config: ConfigManager) -> None:
        self.app = app
        self.config = config
        self.windows: list[MainWindow] = []
        self._last_snapshot: dict[str, Any] | None = None
        self.app.aboutToQuit.connect(self.save_window_states)

    def restore_windows(self) -> None:
        states = self._valid_saved_window_states()
        if not states:
            legacy_folder = str(self.config.get("last_folder", "") or "")
            states = [
                {
                    "folder": legacy_folder if path_exists(legacy_folder) else "",
                    "x": int(self.config.get("window_x", 200) or 200),
                    "y": int(self.config.get("window_y", 200) or 200),
                    "width": int(self.config.get("window_width", 420) or 420),
                    "height": int(self.config.get("window_height", 520) or 520),
                    "always_on_top": bool(self.config.get("always_on_top", False)),
                    "background_opacity": float(
                        self.config.get("background_opacity", self.config.get("window_opacity", 0.72))
                    ),
                    "view_mode": str(self.config.get("view_mode", "icons") or "icons"),
                }
            ]

        for index, state in enumerate(states):
            self.create_window(initial_state=state, offset_index=index, show=True)

    def create_window(
        self,
        initial_state: dict[str, Any] | None = None,
        offset_index: int = 0,
        show: bool = True,
        ask_folder: bool = False,
    ) -> MainWindow:
        window = MainWindow(self.config, manager=self, initial_state=initial_state, instance_offset=offset_index)
        self.windows.append(window)
        if show:
            window.show()
        if ask_folder:
            window.choose_folder()
        return window

    def open_new_window(self) -> None:
        base = self.active_window_state()
        base["folder"] = ""
        base["x"] = int(base.get("x", 200)) + 36
        base["y"] = int(base.get("y", 200)) + 36
        self.create_window(initial_state=base, offset_index=len(self.windows), show=True, ask_folder=True)
        self.save_window_states()

    def unregister_window(self, window: MainWindow) -> None:
        snapshot = window.snapshot_state()
        self._last_snapshot = snapshot
        if window in self.windows:
            self.windows.remove(window)
        self.save_window_states(fallback=snapshot)

    def active_window_state(self) -> dict[str, Any]:
        if self.windows:
            return self.windows[-1].snapshot_state()
        if self._last_snapshot:
            return dict(self._last_snapshot)
        return {
            "folder": "",
            "x": 200,
            "y": 200,
            "width": 420,
            "height": 520,
            "always_on_top": bool(self.config.get("always_on_top", False)),
            "background_opacity": float(self.config.get("background_opacity", 0.72)),
            "view_mode": str(self.config.get("view_mode", "icons") or "icons"),
        }

    def save_window_states(self, fallback: dict[str, Any] | None = None) -> None:
        states = [window.snapshot_state() for window in self.windows if window.isVisible()]
        if not states and fallback:
            states = [fallback]
        elif not states and self._last_snapshot:
            states = [self._last_snapshot]

        self.config.set("windows", states)
        if states:
            first = states[0]
            self.config.update(
                {
                    "last_folder": first.get("folder", ""),
                    "window_x": first.get("x", 200),
                    "window_y": first.get("y", 200),
                    "window_width": first.get("width", 420),
                    "window_height": first.get("height", 520),
                    "always_on_top": first.get("always_on_top", False),
                    "background_opacity": first.get("background_opacity", 0.72),
                    "window_opacity": first.get("background_opacity", 0.72),
                    "view_mode": first.get("view_mode", "icons"),
                }
            )
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
                    "x": int(item.get("x", 200) or 200),
                    "y": int(item.get("y", 200) or 200),
                    "width": int(item.get("width", 420) or 420),
                    "height": int(item.get("height", 520) or 520),
                    "always_on_top": bool(item.get("always_on_top", False)),
                    "background_opacity": float(item.get("background_opacity", self.config.get("background_opacity", 0.72))),
                    "view_mode": str(item.get("view_mode", self.config.get("view_mode", "icons")) or "icons"),
                }
            )
        return states


def create_app(argv: list[str]) -> tuple[QApplication, ConfigManager]:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setOrganizationName("FolderBox")

    icon_path = asset_path("app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    return app, ConfigManager()


def run_app(argv: list[str]) -> int:
    app, config = create_app(argv)
    manager = WindowManager(app, config)
    manager.restore_windows()
    return app.exec()
