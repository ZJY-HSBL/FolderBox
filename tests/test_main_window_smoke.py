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

    window.close()
    app.processEvents()
