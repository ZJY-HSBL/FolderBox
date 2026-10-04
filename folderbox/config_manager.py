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
}

DEFAULT_CONFIG: dict[str, Any] = {"windows": []}


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
            if not isinstance(windows, list):
                raise ValueError("windows must be a list")
            self._config = {"windows": windows}
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            self._config = DEFAULT_CONFIG.copy()
        return self._config

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self._config, file, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
