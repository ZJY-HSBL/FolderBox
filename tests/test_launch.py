from folderbox.launch import requested_folder


def test_requested_folder_accepts_existing_directory(tmp_path) -> None:
    folder = tmp_path / "Research Files"
    folder.mkdir()

    result = requested_folder(["folderbox", "--folder", str(folder)])

    assert result == str(folder.resolve())


def test_requested_folder_rejects_missing_or_file_target(tmp_path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("x", encoding="utf-8")

    assert requested_folder(["folderbox"]) == ""
    assert requested_folder(["folderbox", "--folder"]) == ""
    assert requested_folder(["folderbox", "--folder", str(file_path)]) == ""
