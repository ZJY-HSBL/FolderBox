from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

from folderbox.config_manager import ConfigManager, DEFAULT_WINDOW_STATE
from folderbox.main_window import MainWindow
from folderbox.utils import path_exists


class WindowManager:
    def __init__(self, app: QApplication, config: ConfigManager) -> None:
        self.app = app
        self.config = config
        self.windows: list[MainWindow] = []
        self.app.aboutToQuit.connect(self.save_window_states)

    def restore_windows(self) -> None:
        active_workspace = str(self.config.get("active_workspace", "") or "")
        workspaces = self.config.get("workspaces", {})
        states: list[dict[str, Any]] = []

        if active_workspace and isinstance(workspaces, dict):
            states = self._normalize_window_states(workspaces.get(active_workspace, []))
        if not states:
            states = self._normalize_window_states(self.config.get("windows", []))
        if not states:
            states = [DEFAULT_WINDOW_STATE.copy()]

        for index, state in enumerate(states):
            self.create_window(initial_state=state, offset_index=index, show=True)

    def create_window(
        self,
        initial_state: dict[str, Any] | None = None,
        offset_index: int = 0,
        show: bool = True,
        ask_folder: bool = False,
    ) -> MainWindow:
        window = MainWindow(
            self.config,
            manager=self,
            initial_state=initial_state,
            instance_offset=offset_index,
        )
        self.windows.append(window)
        if show:
            window.show()
        if ask_folder:
            window.choose_folder()
        return window

    def open_new_window(self, source: MainWindow | None = None) -> None:
        if source is not None:
            base = source.snapshot_state()
            base["folder"] = ""
            base["box_title"] = ""
            base["x"] = int(base.get("x", 200)) + 36
            base["y"] = int(base.get("y", 200)) + 36
        else:
            base = DEFAULT_WINDOW_STATE.copy()
            base["x"] = int(base["x"]) + len(self.windows) * 36
            base["y"] = int(base["y"]) + len(self.windows) * 36

        self.create_window(
            initial_state=base,
            offset_index=len(self.windows),
            show=True,
            ask_folder=True,
        )
        self.save_window_states()

    def open_folder_window(self, folder: str) -> bool:
        if not path_exists(folder) or not Path(folder).is_dir():
            return False

        if len(self.windows) == 1 and not self.windows[0].current_folder:
            window = self.windows[0]
            window.set_current_folder(folder)
            window.show()
            window.raise_()
            window.activateWindow()
            self.save_window_states()
            return True

        base = DEFAULT_WINDOW_STATE.copy()
        if self.windows:
            source_state = self.windows[-1].snapshot_state()
            for key in (
                "background_opacity",
                "view_mode",
                "theme_mode",
                "accent_color",
                "icon_size",
            ):
                if key in source_state:
                    base[key] = source_state[key]

        base["folder"] = folder
        base["box_title"] = ""
        base["x"] = int(base["x"]) + len(self.windows) * 36
        base["y"] = int(base["y"]) + len(self.windows) * 36
        window = self.create_window(
            initial_state=base,
            offset_index=len(self.windows),
            show=True,
        )
        window.raise_()
        window.activateWindow()
        self.save_window_states()
        return True

    def handle_external_request(self, folder: str) -> None:
        if folder and self.open_folder_window(folder):
            return
        self.show_all()

    def unregister_window(self, window: MainWindow) -> None:
        if window in self.windows:
            self.windows.remove(window)
        self.save_window_states()

    def snapshot_windows(self) -> list[dict[str, Any]]:
        return [window.snapshot_state() for window in self.windows]

    def save_window_states(self) -> None:
        states = self.snapshot_windows()
        self.config.set("windows", states)

        active_workspace = str(self.config.get("active_workspace", "") or "")
        if active_workspace and states:
            workspaces = dict(self.config.get("workspaces", {}) or {})
            workspaces[active_workspace] = states
            self.config.set("workspaces", workspaces)

        self.config.save()

    def hide_all(self) -> None:
        for window in self.windows:
            window.hide()

    def show_all(self) -> None:
        if not self.windows:
            self.create_window(initial_state=DEFAULT_WINDOW_STATE.copy(), show=True)
        for window in self.windows:
            window.show()
            window.raise_()

    def toggle_all(self) -> None:
        if any(window.isVisible() for window in self.windows):
            self.hide_all()
        else:
            self.show_all()

    def workspace_names(self) -> list[str]:
        workspaces = self.config.get("workspaces", {})
        if not isinstance(workspaces, dict):
            return []
        return sorted(str(name) for name in workspaces if str(name).strip())

    def active_workspace(self) -> str:
        return str(self.config.get("active_workspace", "") or "")

    def save_workspace(self, name: str) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Workspace name cannot be empty.")

        states = self.snapshot_windows()
        if not states:
            raise ValueError("Workspace must contain at least one Box.")

        workspaces = dict(self.config.get("workspaces", {}) or {})
        workspaces[clean_name] = states
        self.config.set("workspaces", workspaces)
        self.config.set("active_workspace", clean_name)
        self.config.set("windows", states)
        self.config.save()

    def load_workspace(self, name: str) -> bool:
        clean_name = name.strip()
        workspaces = self.config.get("workspaces", {})
        if not clean_name or not isinstance(workspaces, dict):
            return False

        states = self._normalize_window_states(workspaces.get(clean_name, []))
        if not states:
            return False

        self.save_window_states()
        old_windows = list(self.windows)
        self.windows.clear()
        for window in old_windows:
            window.hide()
            window.deleteLater()

        self.config.set("active_workspace", clean_name)
        for index, state in enumerate(states):
            self.create_window(initial_state=state, offset_index=index, show=True)
        self.save_window_states()
        return True

    def rename_workspace(self, old_name: str, new_name: str) -> bool:
        old_clean = old_name.strip()
        new_clean = new_name.strip()
        if not old_clean or not new_clean:
            return False

        workspaces = dict(self.config.get("workspaces", {}) or {})
        if old_clean not in workspaces or (new_clean != old_clean and new_clean in workspaces):
            return False
        if new_clean == old_clean:
            return True

        workspaces[new_clean] = workspaces.pop(old_clean)
        self.config.set("workspaces", workspaces)
        if self.active_workspace() == old_clean:
            self.config.set("active_workspace", new_clean)
        self.config.save()
        return True

    def workspace_box_count(self, name: str) -> int:
        workspaces = self.config.get("workspaces", {})
        if not isinstance(workspaces, dict):
            return 0
        states = workspaces.get(name, [])
        return len(states) if isinstance(states, list) else 0

    def delete_workspace(self, name: str) -> bool:
        clean_name = name.strip()
        workspaces = dict(self.config.get("workspaces", {}) or {})
        if clean_name not in workspaces:
            return False

        del workspaces[clean_name]
        self.config.set("workspaces", workspaces)
        if self.active_workspace() == clean_name:
            self.config.set("active_workspace", "")
        self.config.save()
        return True

    def quit(self) -> None:
        self.save_window_states()
        self.app.quit()

    def _normalize_window_states(self, raw_states: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_states, list):
            return []

        states: list[dict[str, Any]] = []
        for item in raw_states:
            if not isinstance(item, dict):
                continue
            folder = str(item.get("folder", "") or "")
            if folder and not path_exists(folder):
                folder = ""
            states.append(
                {
                    "folder": folder,
                    "x": int(item.get("x", DEFAULT_WINDOW_STATE["x"]) or DEFAULT_WINDOW_STATE["x"]),
                    "y": int(item.get("y", DEFAULT_WINDOW_STATE["y"]) or DEFAULT_WINDOW_STATE["y"]),
                    "width": int(
                        item.get("width", DEFAULT_WINDOW_STATE["width"])
                        or DEFAULT_WINDOW_STATE["width"]
                    ),
                    "height": int(
                        item.get("height", DEFAULT_WINDOW_STATE["height"])
                        or DEFAULT_WINDOW_STATE["height"]
                    ),
                    "always_on_top": bool(
                        item.get("always_on_top", DEFAULT_WINDOW_STATE["always_on_top"])
                    ),
                    "background_opacity": float(
                        item.get(
                            "background_opacity",
                            DEFAULT_WINDOW_STATE["background_opacity"],
                        )
                    ),
                    "view_mode": str(
                        item.get("view_mode", DEFAULT_WINDOW_STATE["view_mode"])
                        or DEFAULT_WINDOW_STATE["view_mode"]
                    ),
                    "box_title": str(item.get("box_title", "") or ""),
                    "locked": bool(item.get("locked", False)),
                    "theme_mode": str(
                        item.get("theme_mode", DEFAULT_WINDOW_STATE["theme_mode"])
                        or DEFAULT_WINDOW_STATE["theme_mode"]
                    ),
                    "accent_color": str(
                        item.get("accent_color", DEFAULT_WINDOW_STATE["accent_color"])
                        or DEFAULT_WINDOW_STATE["accent_color"]
                    ),
                    "icon_size": int(
                        item.get("icon_size", DEFAULT_WINDOW_STATE["icon_size"])
                        or DEFAULT_WINDOW_STATE["icon_size"]
                    ),
                }
            )
        return states
