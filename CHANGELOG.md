# Changelog

All notable changes to FolderBox are documented here.

## [1.1.0] - Unreleased

### Changed

- New windows inherit state from the window that created them instead of the most recently created window.
- Configuration writes are atomic to reduce the chance of corruption.
- Window restoration recovers from disconnected or unavailable displays.
- Windows filename validation now handles reserved device names, control characters, and invalid trailing characters.
- Added `python -m folderbox` as a supported launch method.
- Replaced the custom Python installer path with PyInstaller + Inno Setup packaging.
- Added Windows CI with Ruff and pytest.
- Added tag-driven GitHub Release automation.
- Added non-blocking background copy, move, and recycle-bin operations.
- Added cut/paste move semantics across FolderBox windows.
- Added Back, Forward, and Up navigation history.
- Added direct folder creation with Ctrl+Shift+N.

### Removed

- Removed the legacy PySide6 installer implementation.
