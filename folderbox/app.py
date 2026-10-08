from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from folderbox import __app_name__
from folderbox.config_manager import ConfigManager
from folderbox.global_hotkey import GlobalHotkeyController
from folderbox.instance_bridge import InstanceBridge, notify_existing_instance
from folderbox.launch import requested_folder
from folderbox.tray import TrayController
from folderbox.ui.workspace_switcher import WorkspaceSwitcher
from folderbox.utils import is_windows
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
    folder = requested_folder(argv)
    qt_argv = [argv[0]] if argv else ["folderbox"]
    app, config = create_app(qt_argv)

    if notify_existing_instance(folder):
        return 0

    manager = WindowManager(app, config)
    bridge = InstanceBridge(app)
    bridge.requestReceived.connect(manager.handle_external_request)
    if not bridge.listen() and notify_existing_instance(folder):
        return 0

    manager.restore_windows()
    if folder:
        manager.open_folder_window(folder)

    switcher = WorkspaceSwitcher(manager)

    hotkey: GlobalHotkeyController | None = None
    hotkey_active = False
    switcher_hotkey_active = False
    if is_windows():
        hotkey = GlobalHotkeyController(app, manager, switcher.show_switcher)
        hotkey_active = hotkey.register()
        switcher_hotkey_active = hotkey.switcher_registered

    tray: TrayController | None = None
    if TrayController.is_available():
        app.setQuitOnLastWindowClosed(False)
        tray = TrayController(
            app,
            manager,
            global_hotkey_active=hotkey_active,
            workspace_switcher_callback=switcher.show_switcher,
            workspace_switcher_hotkey_active=switcher_hotkey_active,
        )
        tray.show()

    exit_code = app.exec()
    del tray
    del hotkey
    del switcher
    del bridge
    return exit_code


def main() -> int:
    return run_app(sys.argv)
