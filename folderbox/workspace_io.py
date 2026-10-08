from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKSPACE_EXPORT_FORMAT = "folderbox-workspace"
WORKSPACE_EXPORT_VERSION = 1
WORKSPACE_LAYOUT_MODES = {"", "grid", "columns", "rows", "cascade"}


class WorkspaceFileError(ValueError):
    pass


def suggested_workspace_filename(name: str) -> str:
    safe = "".join(
        "_" if character in '<>:"/\\|?*' or ord(character) < 32 else character
        for character in name.strip()
    ).rstrip(". ")
    if not safe:
        safe = "Workspace"
    return f"FolderBox-{safe}.folderbox-workspace.json"


def build_workspace_payload(
    name: str,
    windows: list[dict[str, Any]],
    layout_mode: str = "",
) -> dict[str, Any]:
    clean_name = name.strip()
    if not clean_name:
        raise WorkspaceFileError("Workspace name cannot be empty.")
    if not windows:
        raise WorkspaceFileError("Workspace must contain at least one Box.")
    if layout_mode not in WORKSPACE_LAYOUT_MODES:
        raise WorkspaceFileError("Workspace layout mode is invalid.")

    return {
        "format": WORKSPACE_EXPORT_FORMAT,
        "version": WORKSPACE_EXPORT_VERSION,
        "name": clean_name,
        "layout_mode": layout_mode,
        "windows": [dict(state) for state in windows],
    }


def write_workspace_file(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_workspace_file(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceFileError(f"Unable to read Workspace file: {exc}") from exc

    if not isinstance(raw, dict):
        raise WorkspaceFileError("Workspace file root must be an object.")
    if raw.get("format") != WORKSPACE_EXPORT_FORMAT:
        raise WorkspaceFileError("Unsupported Workspace file format.")
    if raw.get("version") != WORKSPACE_EXPORT_VERSION:
        raise WorkspaceFileError("Unsupported Workspace file version.")

    name = str(raw.get("name", "") or "").strip()
    windows = raw.get("windows", [])
    layout_mode = str(raw.get("layout_mode", "") or "")

    if not name:
        raise WorkspaceFileError("Workspace file has no name.")
    if not isinstance(windows, list) or not windows:
        raise WorkspaceFileError("Workspace file must contain at least one Box.")
    if any(not isinstance(state, dict) for state in windows):
        raise WorkspaceFileError("Workspace Box states must be objects.")
    if layout_mode not in WORKSPACE_LAYOUT_MODES:
        raise WorkspaceFileError("Workspace file contains an invalid layout mode.")

    return {
        "name": name,
        "layout_mode": layout_mode,
        "windows": [dict(state) for state in windows],
    }
