from folderbox.startup import build_startup_command


def test_frozen_startup_command_only_launches_executable(tmp_path) -> None:
    executable = tmp_path / "Folder Box.exe"

    command = build_startup_command(executable, frozen=True)

    assert "Folder Box.exe" in command
    assert "-m folderbox" not in command


def test_development_startup_prefers_pythonw(tmp_path) -> None:
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_text("", encoding="utf-8")
    pythonw.write_text("", encoding="utf-8")

    command = build_startup_command(python, frozen=False)

    assert "pythonw.exe" in command
    assert "-m folderbox" in command
