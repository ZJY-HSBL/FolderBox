import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager
from folderbox.ui.workspace_dialog import WorkspaceDialog
from folderbox.window_manager import WindowManager


class FakeWindow:
    def __init__(self, state: dict) -> None:
        self.state = state

    def snapshot_state(self) -> dict:
        return dict(self.state)


def test_workspace_dialog_lists_saved_layouts(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(app, config)

    manager.windows = [FakeWindow({"folder": "A"}), FakeWindow({"folder": "B"})]
    manager.save_workspace("Research")

    dialog = WorkspaceDialog(manager)

    assert dialog.list_widget.count() == 1
    assert "Research" in dialog.list_widget.item(0).text()
    assert "2 个 Box" in dialog.list_widget.item(0).text()
    assert "当前" in dialog.list_widget.item(0).text()
    assert dialog.update_button.isEnabled()

    dialog.close()
    app.processEvents()



def test_workspace_dialog_exposes_layout_templates(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(app, config)

    arranged: list[str] = []
    manager.arrange_visible = lambda mode: arranged.append(mode) or 0

    dialog = WorkspaceDialog(manager)

    assert dialog.arrange_combo.count() == 4
    assert dialog.arrange_combo.itemData(0) == "grid"
    assert dialog.arrange_combo.itemData(1) == "columns"
    assert dialog.arrange_combo.itemData(2) == "rows"
    assert dialog.arrange_combo.itemData(3) == "cascade"

    dialog.arrange_combo.setCurrentIndex(3)
    dialog.arrange_current()

    assert arranged == ["cascade"]

    dialog.close()
    app.processEvents()



def test_workspace_dialog_edits_default_layout_policy(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(app, config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    dialog = WorkspaceDialog(manager)

    assert dialog.layout_policy_combo.count() == 5
    assert dialog.layout_policy_combo.itemData(0) == ""
    grid_index = dialog.layout_policy_combo.findData("grid")
    dialog.layout_policy_combo.setCurrentIndex(grid_index)
    dialog.save_layout_policy()

    assert manager.workspace_layout_mode("Research") == "grid"
    assert "自动：均衡网格" in dialog.list_widget.item(0).text()

    dialog.close()
    app.processEvents()
