import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager
from folderbox.ui.workspace_switcher import WorkspaceSwitcher
from folderbox.window_manager import WindowManager


class FakeWindow:
    def __init__(self, state: dict) -> None:
        self.state = state

    def snapshot_state(self) -> dict:
        return dict(self.state)


def _manager_with_workspaces(tmp_path):
    app = QApplication.instance() or QApplication([])
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(app, config)

    manager.windows = [FakeWindow({"folder": "A"})]
    manager.save_workspace("Research")
    manager.set_workspace_layout_mode("Research", "grid")
    manager.set_workspace_hotkey_slot("Research", 1)

    manager.windows = [FakeWindow({"folder": "B"}), FakeWindow({"folder": "C"})]
    manager.save_workspace("Coding")
    return app, manager


def test_switcher_lists_workspace_metadata(tmp_path) -> None:
    app, manager = _manager_with_workspaces(tmp_path)
    switcher = WorkspaceSwitcher(manager)
    switcher.refresh()

    assert switcher.list_widget.count() == 2
    texts = [switcher.list_widget.item(i).text() for i in range(2)]
    research = next(text for text in texts if "Research" in text)

    assert "1 个 Box" in research
    assert "网格" in research
    assert "Ctrl+Alt+1" in research

    switcher.close()
    app.processEvents()


def test_switcher_filters_workspace_names(tmp_path) -> None:
    app, manager = _manager_with_workspaces(tmp_path)
    switcher = WorkspaceSwitcher(manager)
    switcher.refresh()

    switcher.search_edit.setText("rese")

    visible = [
        switcher.list_widget.item(i).data(0x0100)
        for i in range(switcher.list_widget.count())
        if not switcher.list_widget.item(i).isHidden()
    ]
    assert visible == ["Research"]

    switcher.close()
    app.processEvents()


def test_switcher_activates_selected_workspace(tmp_path) -> None:
    app, manager = _manager_with_workspaces(tmp_path)
    loaded: list[str] = []
    manager.load_workspace = lambda name: loaded.append(name) or True

    switcher = WorkspaceSwitcher(manager)
    switcher.refresh()
    for index in range(switcher.list_widget.count()):
        item = switcher.list_widget.item(index)
        if item.data(0x0100) == "Research":
            switcher.list_widget.setCurrentItem(item)
            break

    switcher.activate_selected()

    assert loaded == ["Research"]

    switcher.close()
    app.processEvents()


def test_switcher_moves_only_across_visible_rows(tmp_path) -> None:
    app, manager = _manager_with_workspaces(tmp_path)
    switcher = WorkspaceSwitcher(manager)
    switcher.refresh()
    switcher.search_edit.setText("research")

    selected_before = switcher.selected_name()
    switcher._move_selection(1)

    assert selected_before == "Research"
    assert switcher.selected_name() == "Research"

    switcher.close()
    app.processEvents()
