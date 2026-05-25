from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "last_folder": "",
    "window_x": 200,
    "window_y": 200,
    "window_width": 420,
    "window_height": 520,
    "always_on_top": False,
    "window_opacity": 0.9,
    "background_opacity": 0.72,
    "view_mode": "icons",
    "windows": [],
}


class ConfigManager:
    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path:
            self.config_path = Path(config_path)
        else:
            app_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
            self.config_path = app_root / "config" / "config.json"
        self._config: dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> dict[str, Any]:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            return self._config

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            if not isinstance(loaded, dict):
                raise ValueError("config root must be an object")
        except (OSError, json.JSONDecodeError, ValueError):
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            return self._config

        changed = False
        merged = DEFAULT_CONFIG.copy()
        for key, value in loaded.items():
            if key in DEFAULT_CONFIG:
                merged[key] = value
        for key in DEFAULT_CONFIG:
            if key not in loaded:
                changed = True

        self._config = merged
        if changed:
            self.save()
        return self._config

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self._config, file, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self._config.update(values)
