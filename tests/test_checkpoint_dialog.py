import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager
from folderbox.ui.checkpoint_dialog import WorkspaceCheckpointDialog
from folderbox.window_manager import WindowManager


class FakeWindow:
    def __init__(self, state: dict) -> None:
        self.state = state

    def snapshot_state(self) -> dict:
        return dict(self.state)


def test_checkpoint_dialog_lists_saved_restore_points(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(app, config)
    manager.windows = [FakeWindow({"folder": "D:/Research", "x": 42})]
    manager.save_workspace("Research")
    manager.create_workspace_checkpoint("Research", "Stable")

    dialog = WorkspaceCheckpointDialog(manager, "Research")

    assert dialog.list_widget.count() == 1
    assert "Stable" in dialog.list_widget.item(0).text()
    assert "1 个 Box" in dialog.list_widget.item(0).text()
    assert dialog.restore_button.isEnabled()
    assert dialog.delete_button.isEnabled()

    dialog.close()
    app.processEvents()
