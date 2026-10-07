from folderbox.config_manager import ConfigManager
from folderbox.window_manager import WindowManager


class FakeSignal:
    def connect(self, callback) -> None:
        self.callback = callback


class FakeApp:
    def __init__(self) -> None:
        self.aboutToQuit = FakeSignal()


class FakeWindow:
    def __init__(self, state: dict) -> None:
        self.state = state

    def snapshot_state(self) -> dict:
        return dict(self.state)


def test_save_window_states_keeps_all_managed_boxes(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [
        FakeWindow({"folder": "A", "box_title": "One"}),
        FakeWindow({"folder": "B", "box_title": "Two"}),
    ]

    manager.save_window_states()

    assert config.get("windows") == [
        {"folder": "A", "box_title": "One"},
        {"folder": "B", "box_title": "Two"},
    ]


def test_save_workspace_sets_active_workspace(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [
        FakeWindow({"folder": "D:/Research", "box_title": "Papers", "locked": True})
    ]

    manager.save_workspace("Research")

    assert manager.active_workspace() == "Research"
    assert manager.workspace_names() == ["Research"]
    assert config.get("workspaces")["Research"][0]["box_title"] == "Papers"


def test_delete_workspace_does_not_delete_window_state(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    assert manager.delete_workspace("Research")
    assert manager.workspace_names() == []
    assert config.get("windows") == [{"folder": "D:/Research"}]



def test_save_workspace_rejects_empty_layout(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)

    try:
        manager.save_workspace("Empty")
    except ValueError as exc:
        assert "at least one Box" in str(exc)
    else:
        raise AssertionError("Expected empty workspace save to fail")
