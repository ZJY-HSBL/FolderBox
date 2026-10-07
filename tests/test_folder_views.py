from pathlib import Path

from folderbox.ui.folder_views import local_file_mime_data


def test_local_file_mime_data_exports_file_urls(tmp_path) -> None:
    first = tmp_path / "one.txt"
    second = tmp_path / "folder"
    first.write_text("x", encoding="utf-8")
    second.mkdir()

    mime_data = local_file_mime_data([str(first), str(second)])

    paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
    assert paths == [first, second]
    assert mime_data.hasUrls()
