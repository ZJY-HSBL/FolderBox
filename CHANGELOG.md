# Changelog

All notable changes to FolderBox are documented here.

## [1.6.0] - 2026-10-08

### Added

- Added per-Workspace automatic layout policies.
- Added default layout choices for saved position, balanced grid, horizontal columns, vertical rows, and cascade.
- Added Workspace manager controls for assigning or clearing automatic layout behavior.
- Added Workspace list indicators that show the active automatic layout policy.

### Changed

- Loading or cycling to a Workspace now reapplies its configured layout policy after restoring Boxes.
- Workspace rename and delete operations now keep layout-policy metadata consistent.

## [1.5.0] - 2026-10-08

### Added

- Added per-Box edge auto-hide with hover-to-expand behavior.
- Added a compact edge trigger strip that keeps auto-hidden Boxes reachable without changing their actual window size.
- Added persisted `edge_peek_enabled` state to individual Boxes and Workspaces.

### Changed

- Edge-peek collapse is runtime-only; saved geometry always uses the expanded Box position.
- Global show-all, Explorer/IPC folder opens, manual placement, and automatic arrangement force edge-peek Boxes back to their expanded geometry first.
- Edge-peek collapse is delayed after pointer leave to reduce accidental hiding and is suppressed while popup menus are active.

## [1.4.0] - 2026-10-08

### Added

- Added multi-Box layout templates for balanced grid, horizontal columns, vertical rows, and cascade arrangements.
- Added one-click layout template actions to the system tray.
- Added current-desktop arrangement controls to the Workspace manager.
- Added multi-monitor-aware arrangement so each screen organizes only its own visible, unlocked Boxes.

### Changed

- Dense row/column layouts automatically wrap when equal cells would fall below FolderBox minimum usable dimensions.
- Locked Boxes are excluded from automatic multi-Box arrangement.
- Multi-Box geometry generation is centralized in the desktop layout module.

## [1.3.0] - 2026-10-08

### Added

- Added automatic Box snapping to screen edges and neighboring Boxes.
- Added one-click Box placement commands for left, right, top, bottom, and screen center.
- Added a tray toggle for enabling or disabling desktop snapping globally.
- Added quick previous/next Workspace switching from the tray.
- Added the Windows global hotkey `Ctrl+Alt+B` to hide or show all Boxes.

### Changed

- Box positions are saved once when a title-bar drag finishes instead of during every drag movement.
- Desktop layout calculations are centralized in a reusable geometry module.

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
