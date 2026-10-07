from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from folderbox import __app_name__
from folderbox.config_manager import ConfigManager
from folderbox.tray import TrayController
from folderbox.window_manager import WindowManager


def asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / name  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "assets" / name


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

    tray: TrayController | None = None
    if TrayController.is_available():
        app.setQuitOnLastWindowClosed(False)
        tray = TrayController(app, manager)
        tray.show()

    exit_code = app.exec()
    del tray
    return exit_code


def main() -> int:
    return run_app(sys.argv)
