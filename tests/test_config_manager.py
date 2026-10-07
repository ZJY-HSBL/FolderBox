import json

from folderbox.config_manager import ConfigManager


def test_save_and_reload_config(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)
    manager.set("windows", [{"folder": "D:/Work", "x": 12, "y": 34}])
    manager.save()

    reloaded = ConfigManager(config_path)
    assert reloaded.get("windows") == [{"folder": "D:/Work", "x": 12, "y": 34}]
    assert not (tmp_path / "config.json.tmp").exists()


def test_corrupt_config_falls_back_to_defaults(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{broken json", encoding="utf-8")

    manager = ConfigManager(config_path)

    assert manager.get("windows") == []


def test_saved_config_is_valid_json(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)
    manager.set("windows", [])
    manager.save()

    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "windows": [],
        "workspaces": {},
        "active_workspace": "",
        "snap_enabled": True,
    }


def test_workspace_state_round_trip(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)
    workspace = {
        "Research": [
            {
                "folder": "D:/Research",
                "box_title": "Papers",
                "locked": True,
            }
        ]
    }
    manager.set("workspaces", workspace)
    manager.set("active_workspace", "Research")
    manager.save()

    reloaded = ConfigManager(config_path)

    assert reloaded.get("workspaces") == workspace
    assert reloaded.get("active_workspace") == "Research"
