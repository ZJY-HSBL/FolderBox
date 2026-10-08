import json

from folderbox.workspace_io import (
    WorkspaceFileError,
    build_workspace_payload,
    read_workspace_file,
    suggested_workspace_filename,
    write_workspace_file,
)


def test_workspace_file_round_trip(tmp_path) -> None:
    path = tmp_path / "Research.folderbox-workspace.json"
    payload = build_workspace_payload(
        "Research",
        [{"folder": "D:/Research", "box_title": "Papers"}],
        "grid",
    )

    write_workspace_file(path, payload)
    loaded = read_workspace_file(path)

    assert loaded == {
        "name": "Research",
        "layout_mode": "grid",
        "windows": [{"folder": "D:/Research", "box_title": "Papers"}],
    }


def test_workspace_file_rejects_wrong_format(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text(
        json.dumps(
            {
                "format": "other",
                "version": 1,
                "name": "Research",
                "windows": [{}],
            }
        ),
        encoding="utf-8",
    )

    try:
        read_workspace_file(path)
    except WorkspaceFileError as exc:
        assert "format" in str(exc)
    else:
        raise AssertionError("Expected unsupported Workspace format to fail")


def test_workspace_file_rejects_invalid_layout_mode() -> None:
    try:
        build_workspace_payload("Research", [{}], "spiral")
    except WorkspaceFileError as exc:
        assert "layout mode" in str(exc)
    else:
        raise AssertionError("Expected invalid Workspace layout mode to fail")


def test_suggested_workspace_filename_is_windows_safe() -> None:
    filename = suggested_workspace_filename('Research: Papers? <2026>')

    assert filename == "FolderBox-Research_ Papers_ _2026_.folderbox-workspace.json"
    assert ":" not in filename
    assert "?" not in filename
