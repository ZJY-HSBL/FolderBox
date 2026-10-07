from folderbox.global_hotkey import (
    HOTKEY_VK,
    MOD_ALT,
    MOD_CONTROL,
    GlobalHotkeyController,
)


def test_global_hotkey_definition() -> None:
    assert GlobalHotkeyController.description() == "Ctrl+Alt+B"
    assert HOTKEY_VK == ord("B")
    assert MOD_CONTROL != 0
    assert MOD_ALT != 0
