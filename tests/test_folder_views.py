from pathlib import Path

from folderbox.ui.folder_views import build_file_mime_data


def test_file_drag_mime_data_contains_local_urls(tmp_path) -> None:
    first = tmp_path / "one.txt"
    second = tmp_path / "two.txt"
    first.write_text("1", encoding="utf-8")
    second.write_text("2", encoding="utf-8")

    mime_data = build_file_mime_data([str(first), str(second)])
    actual_paths = [Path(url.toLocalFile()).resolve() for url in mime_data.urls()]

    assert mime_data.hasUrls()
    assert actual_paths == [first.resolve(), second.resolve()]


def test_file_drag_mime_data_ignores_missing_paths(tmp_path) -> None:
    mime_data = build_file_mime_data([str(tmp_path / "missing.txt")])

    assert not mime_data.hasUrls()
    assert mime_data.urls() == []
