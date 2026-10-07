from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QSystemTrayIcon

from folderbox.shell_integration import (
    ShellIntegrationError,
    is_shell_integration_enabled,
    set_shell_integration_enabled,
)
from folderbox.startup import StartupError, is_startup_enabled, set_startup_enabled
from folderbox.ui.workspace_dialog import WorkspaceDialog
from folderbox.window_manager import WindowManager


class TrayController:
    def __init__(self, app: QApplication, manager: WindowManager) -> None:
        self.app = app
        self.manager = manager
        self.tray = QSystemTrayIcon(app.windowIcon(), app)
        self.menu = QMenu()

        self.toggle_action = QAction("隐藏 / 显示全部 Box", self.menu)
        self.new_box_action = QAction("新建 Box", self.menu)
        self.workspace_menu = self.menu.addMenu("工作区")
        self.save_workspace_action = QAction("保存当前工作区…", self.menu)
        self.manage_workspaces_action = QAction("管理工作区…", self.menu)
        self.startup_action = QAction("开机启动", self.menu)
        self.startup_action.setCheckable(True)
        self.shell_action = QAction("资源管理器右键菜单", self.menu)
        self.shell_action.setCheckable(True)
        self.quit_action = QAction("退出 FolderBox", self.menu)

        self.menu.insertAction(self.workspace_menu.menuAction(), self.toggle_action)
        self.menu.insertAction(self.workspace_menu.menuAction(), self.new_box_action)
        self.menu.insertSeparator(self.workspace_menu.menuAction())
        self.menu.addSeparator()
        self.menu.addAction(self.startup_action)
        self.menu.addAction(self.shell_action)
        self.menu.addAction(self.quit_action)

        self.toggle_action.triggered.connect(self.manager.toggle_all)
        self.new_box_action.triggered.connect(lambda: self.manager.open_new_window(None))
        self.save_workspace_action.triggered.connect(self.save_workspace)
        self.manage_workspaces_action.triggered.connect(self.manage_workspaces)
        self.startup_action.triggered.connect(self.set_startup)
        self.shell_action.triggered.connect(self.set_shell_integration)
        self.quit_action.triggered.connect(self.manager.quit)
        self.menu.aboutToShow.connect(self.refresh_workspace_menu)
        self.tray.activated.connect(self._on_activated)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("FolderBox")
        self._workspace_dialog: WorkspaceDialog | None = None

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self) -> None:
        self.refresh_workspace_menu()
        self.tray.show()

    def refresh_workspace_menu(self) -> None:
        self.startup_action.blockSignals(True)
        self.startup_action.setChecked(is_startup_enabled())
        self.startup_action.blockSignals(False)
        self.shell_action.blockSignals(True)
        self.shell_action.setChecked(is_shell_integration_enabled())
        self.shell_action.blockSignals(False)

        self.workspace_menu.clear()
        self.workspace_menu.addAction(self.save_workspace_action)
        self.workspace_menu.addAction(self.manage_workspaces_action)
        self.workspace_menu.addSeparator()

        names = self.manager.workspace_names()
        active = self.manager.active_workspace()
        if not names:
            empty_action = self.workspace_menu.addAction("暂无已保存工作区")
            empty_action.setEnabled(False)
            return

        for name in names:
            action = self.workspace_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(name == active)
            action.triggered.connect(lambda checked=False, value=name: self.load_workspace(value))

    def save_workspace(self) -> None:
        current = self.manager.active_workspace()
        name, ok = QInputDialog.getText(
            None,
            "保存工作区",
            "工作区名称：",
            text=current,
        )
        if not ok or not name.strip():
            return
        try:
            self.manager.save_workspace(name)
        except ValueError as exc:
            QMessageBox.warning(None, "保存工作区失败", str(exc))
            return
        self.refresh_workspace_menu()

    def manage_workspaces(self) -> None:
        if self._workspace_dialog is None:
            self._workspace_dialog = WorkspaceDialog(self.manager)
            self._workspace_dialog.finished.connect(self._release_workspace_dialog)
        self._workspace_dialog.refresh()
        self._workspace_dialog.show()
        self._workspace_dialog.raise_()
        self._workspace_dialog.activateWindow()

    def _release_workspace_dialog(self, result: int = 0) -> None:
        if self._workspace_dialog is not None:
            self._workspace_dialog.deleteLater()
            self._workspace_dialog = None
        self.refresh_workspace_menu()

    def load_workspace(self, name: str) -> None:
        if not self.manager.load_workspace(name):
            QMessageBox.warning(None, "切换工作区失败", f"无法加载工作区：{name}")
        self.refresh_workspace_menu()

    def set_startup(self, enabled: bool) -> None:
        try:
            set_startup_enabled(enabled)
        except StartupError as exc:
            self.startup_action.blockSignals(True)
            self.startup_action.setChecked(is_startup_enabled())
            self.startup_action.blockSignals(False)
            QMessageBox.warning(None, "开机启动设置失败", str(exc))

    def set_shell_integration(self, enabled: bool) -> None:
        try:
            set_shell_integration_enabled(enabled)
        except ShellIntegrationError as exc:
            self.shell_action.blockSignals(True)
            self.shell_action.setChecked(is_shell_integration_enabled())
            self.shell_action.blockSignals(False)
            QMessageBox.warning(None, "资源管理器右键菜单设置失败", str(exc))

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.manager.toggle_all()
