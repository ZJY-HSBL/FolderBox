from folderbox.shell_integration import build_shell_command


def test_frozen_shell_command_quotes_target_placeholder(tmp_path) -> None:
    executable = tmp_path / "Folder Box.exe"

    command = build_shell_command(executable, frozen=True, placeholder="%1")

    assert "Folder Box.exe" in command
    assert '--folder "%1"' in command
    assert "-m folderbox" not in command


def test_development_shell_command_uses_module_entrypoint(tmp_path) -> None:
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_text("", encoding="utf-8")
    pythonw.write_text("", encoding="utf-8")

    command = build_shell_command(python, frozen=False, placeholder="%V")

    assert "pythonw.exe" in command
    assert "-m folderbox" in command
    assert '--folder "%V"' in command
