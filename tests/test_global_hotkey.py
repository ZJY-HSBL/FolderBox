from folderbox.global_hotkey import (
    MOD_ALT,
    MOD_CONTROL,
    SWITCHER_HOTKEY_VK,
    TOGGLE_HOTKEY_VK,
    GlobalHotkeyController,
    workspace_hotkey_id,
    workspace_hotkey_vk,
)


def test_global_hotkey_definition() -> None:
    assert GlobalHotkeyController.description() == "Ctrl+Alt+B"
    assert GlobalHotkeyController.switcher_description() == "Ctrl+Alt+Space"
    assert TOGGLE_HOTKEY_VK == ord("B")
    assert SWITCHER_HOTKEY_VK == 0x20
    assert MOD_CONTROL != 0
    assert MOD_ALT != 0


def test_workspace_hotkey_helpers() -> None:
    assert GlobalHotkeyController.workspace_description(1) == "Ctrl+Alt+1"
    assert GlobalHotkeyController.workspace_description(9) == "Ctrl+Alt+9"
    assert workspace_hotkey_vk(4) == ord("4")
    assert workspace_hotkey_id(1) != workspace_hotkey_id(2)


def test_workspace_hotkey_rejects_invalid_slot() -> None:
    try:
        workspace_hotkey_vk(0)
    except ValueError as exc:
        assert "between 1 and 9" in str(exc)
    else:
        raise AssertionError("Expected invalid Workspace hotkey slot to fail")
