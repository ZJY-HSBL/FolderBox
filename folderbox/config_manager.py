from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QStandardPaths


DEFAULT_WINDOW_STATE: dict[str, Any] = {
    "folder": "",
    "x": 200,
    "y": 200,
    "width": 420,
    "height": 520,
    "always_on_top": False,
    "background_opacity": 0.72,
    "view_mode": "icons",
    "box_title": "",
    "locked": False,
    "theme_mode": "light",
    "accent_color": "#3b82f6",
    "icon_size": 40,
}

DEFAULT_CONFIG: dict[str, Any] = {
    "windows": [],
    "workspaces": {},
    "active_workspace": "",
    "snap_enabled": True,
}


class ConfigManager:
    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is not None:
            self.config_path = Path(config_path)
        else:
            root = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
            self.config_path = root / "config.json"
        self._config: dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> dict[str, Any]:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            return self._config

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            windows = loaded.get("windows", [])
            workspaces = loaded.get("workspaces", {})
            active_workspace = loaded.get("active_workspace", "")
            snap_enabled = loaded.get("snap_enabled", True)
            if not isinstance(windows, list):
                raise ValueError("windows must be a list")
            if not isinstance(workspaces, dict):
                raise ValueError("workspaces must be an object")
            if not isinstance(active_workspace, str):
                raise ValueError("active_workspace must be a string")
            if not isinstance(snap_enabled, bool):
                raise ValueError("snap_enabled must be a boolean")
            self._config = {
                "windows": windows,
                "workspaces": workspaces,
                "active_workspace": active_workspace,
                "snap_enabled": snap_enabled,
            }
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            self._config = DEFAULT_CONFIG.copy()
        return self._config

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.config_path.with_suffix(self.config_path.suffix + ".tmp")
        payload = json.dumps(self._config, ensure_ascii=False, indent=2)
        try:
            temporary_path.write_text(payload, encoding="utf-8")
            temporary_path.replace(self.config_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
