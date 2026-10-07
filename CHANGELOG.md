# Changelog

All notable changes to FolderBox are documented here.

## [1.2.0] - 2026-10-08

### Added

- Added per-Box light and dark themes.
- Added per-Box accent colors with presets and a custom color picker.
- Added configurable icon sizes for icon view.
- Added a visual Workspace manager for switching, saving, renaming, and deleting layouts.
- Added optional Windows Explorer context-menu integration for opening folders in FolderBox.
- Added single-instance local IPC so Explorer launches are routed to the running FolderBox process.
- Added explicit multi-selection drag-out support using standard local file URLs.
- Added Ctrl + mouse-wheel icon zoom for icon view.

### Changed

- Consolidated Workspace management into one dedicated dialog while keeping quick switching in the tray.
- External folder requests reuse an empty Box when possible and otherwise open a managed Box that inherits appearance settings.
- Consolidated icon/detail drag behavior into a shared file-view drag/drop layer.

### Fixed

- Improved repeated-launch behavior by routing new folder requests to the existing FolderBox process instead of creating duplicate tray instances.
- Preserved per-Box appearance and layout state when folders are opened from Windows Explorer.

## [1.1.0] - 2026-10-07

### Added

- Added non-blocking background copy, move, and recycle-bin operations.
- Added cut/paste move semantics across FolderBox windows.
- Added direct folder creation with `Ctrl+Shift+N`.
- Added Back, Forward, Up, and clickable breadcrumb navigation.
- Added current-folder name filtering with optional `*` and `?` wildcard patterns.
- Added a Windows system tray with global hide/show, new Box, Workspace, startup, and quit controls.
- Added named Workspaces for saving and restoring complete multi-Box desktop layouts.
- Added per-Box custom titles and layout locking.
- Added Windows launch-at-login support through the current-user Run key.
- Added `python -m folderbox` as a supported launch method.
- Added Windows CI on Python 3.10 and 3.12.
- Added repeatable packaging smoke tests and tag-driven GitHub Release automation.
- Added automated installer, portable archive, and SHA256 checksum generation.

### Changed

- Repositioned FolderBox as a lightweight persistent folder portal for the Windows desktop.
- Split the crowded window chrome into a compact title bar and dedicated navigation row.
- Moved low-frequency Box controls into a compact overflow menu.
- New windows inherit state from the Box that created them instead of the most recently created window.
- Configuration writes are atomic to reduce the chance of corruption.
- Window restoration recovers from disconnected or unavailable displays.
- Hidden Boxes remain part of persisted state instead of being treated as closed windows.
- Windows filename validation now handles reserved device names, control characters, and invalid trailing characters.
- File counts now reflect the active current-folder filter.
- Extracted window lifecycle management, folder view widgets, theme styling, and reusable background task execution into dedicated modules.
- Replaced the custom Python installer with PyInstaller + Inno Setup packaging.

### Fixed

- Fixed stale clipboard ownership after move operations.
- Fixed GUI-thread safety for background file-operation callbacks.
- Fixed stale launch-at-login registrations after a portable executable is moved.
- Fixed new-window state inheritance when opening a Box from an older window.

### Removed

- Removed the legacy PySide6 installer implementation.
- Removed obsolete legacy configuration writes and shortened-path UI logic.
