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



def test_empty_window_state_does_not_erase_active_workspace(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research", "box_title": "Papers"})]
    manager.save_workspace("Research")

    manager.windows = []
    manager.save_window_states()

    assert config.get("windows") == []
    assert config.get("workspaces")["Research"] == [
        {"folder": "D:/Research", "box_title": "Papers"}
    ]



def test_rename_workspace_preserves_active_state(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    assert manager.rename_workspace("Research", "Papers")
    assert manager.active_workspace() == "Papers"
    assert manager.workspace_names() == ["Papers"]
    assert manager.workspace_box_count("Papers") == 1


def test_rename_workspace_rejects_duplicate_name(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "A"})]
    manager.save_workspace("One")
    manager.windows = [FakeWindow({"folder": "B"})]
    manager.save_workspace("Two")

    assert not manager.rename_workspace("One", "Two")
    assert manager.workspace_names() == ["One", "Two"]



def test_snap_preference_round_trip(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)

    assert manager.is_snap_enabled()
    manager.set_snap_enabled(False)

    assert not manager.is_snap_enabled()
    assert ConfigManager(tmp_path / "config.json").get("snap_enabled") is False


def test_cycle_workspace_wraps_names(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    config.set("workspaces", {"One": [{}], "Two": [{}]})
    config.set("active_workspace", "Two")

    loaded: list[str] = []
    manager.load_workspace = lambda name: loaded.append(name) or True

    assert manager.cycle_workspace(1)
    assert loaded == ["One"]



def test_normalized_workspace_preserves_edge_peek_preference(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)

    states = manager._normalize_window_states(
        [{"folder": "", "edge_peek_enabled": True}]
    )

    assert states[0]["edge_peek_enabled"] is True



def test_workspace_layout_policy_can_be_set_and_cleared(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    assert manager.set_workspace_layout_mode("Research", "grid")
    assert manager.workspace_layout_mode("Research") == "grid"

    assert manager.set_workspace_layout_mode("Research", None)
    assert manager.workspace_layout_mode("Research") == ""


def test_workspace_layout_policy_rejects_unknown_modes(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    assert not manager.set_workspace_layout_mode("Research", "spiral")
    assert manager.workspace_layout_mode("Research") == ""


def test_workspace_rename_moves_layout_policy(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")
    manager.set_workspace_layout_mode("Research", "columns")

    assert manager.rename_workspace("Research", "Papers")
    assert manager.workspace_layout_mode("Research") == ""
    assert manager.workspace_layout_mode("Papers") == "columns"


def test_workspace_delete_removes_layout_policy(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")
    manager.set_workspace_layout_mode("Research", "rows")

    assert manager.delete_workspace("Research")
    assert config.get("workspace_layouts") == {}


def test_workspace_load_applies_saved_layout_policy(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    config.set("workspaces", {"Research": [{"folder": ""}]})
    config.set("workspace_layouts", {"Research": "cascade"})

    created: list[dict] = []
    arranged: list[str] = []
    manager.create_window = lambda initial_state, offset_index, show: created.append(initial_state)
    manager.arrange_visible = lambda mode: arranged.append(mode) or 1

    assert manager.load_workspace("Research")
    assert created == [{"folder": "", "x": 200, "y": 200, "width": 420, "height": 520, "always_on_top": False, "background_opacity": 0.72, "view_mode": "icons", "box_title": "", "locked": False, "theme_mode": "light", "accent_color": "#3b82f6", "icon_size": 40, "edge_peek_enabled": False}]
    assert arranged == ["cascade"]



def test_workspace_hotkey_slot_can_be_set_and_cleared(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")

    assert manager.set_workspace_hotkey_slot("Research", 1)
    assert manager.workspace_hotkey_slot("Research") == 1
    assert manager.workspace_hotkey_bindings() == {1: "Research"}

    assert manager.set_workspace_hotkey_slot("Research", None)
    assert manager.workspace_hotkey_slot("Research") == 0


def test_workspace_hotkey_slots_are_unique(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "A"})]
    manager.save_workspace("One")
    manager.windows = [FakeWindow({"folder": "B"})]
    manager.save_workspace("Two")

    assert manager.set_workspace_hotkey_slot("One", 2)
    assert not manager.set_workspace_hotkey_slot("Two", 2)
    assert manager.workspace_hotkey_bindings() == {2: "One"}


def test_workspace_rename_moves_hotkey_binding(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")
    manager.set_workspace_hotkey_slot("Research", 3)

    assert manager.rename_workspace("Research", "Papers")
    assert manager.workspace_hotkey_slot("Research") == 0
    assert manager.workspace_hotkey_slot("Papers") == 3


def test_workspace_delete_removes_hotkey_binding(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    manager.windows = [FakeWindow({"folder": "D:/Research"})]
    manager.save_workspace("Research")
    manager.set_workspace_hotkey_slot("Research", 4)

    assert manager.delete_workspace("Research")
    assert config.get("workspace_hotkeys") == {}


def test_workspace_hotkey_loads_bound_workspace(tmp_path) -> None:
    config = ConfigManager(tmp_path / "config.json")
    manager = WindowManager(FakeApp(), config)
    config.set("workspaces", {"Research": [{}]})
    config.set("workspace_hotkeys", {"Research": 5})

    loaded: list[str] = []
    manager.load_workspace = lambda name: loaded.append(name) or True

    assert manager.load_workspace_by_hotkey(5)
    assert loaded == ["Research"]
