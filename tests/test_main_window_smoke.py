import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager
from folderbox.main_window import MainWindow


def test_main_window_builds_product_chrome(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    window = MainWindow(config)

    assert window.title_label.text() == "FolderBox"
    assert window.more_button.menu() is window.more_menu
    assert window.search_edit.placeholderText()
    assert window.breadcrumb is not None
    assert window.view_button.icon().isNull() is False
    assert window.min_button.icon().isNull() is False
    assert window.close_button.icon().isNull() is False
    assert window.theme_mode == "light"
    assert window.accent_color == "#3b82f6"
    assert window.icon_size == 40

    window._apply_theme_mode("dark")
    window._apply_accent_color("#8b5cf6")
    window._apply_icon_size(56)
    state = window.snapshot_state()

    assert state["theme_mode"] == "dark"
    assert state["accent_color"] == "#8b5cf6"
    assert state["icon_size"] == 56

    window.close()
    app.processEvents()
