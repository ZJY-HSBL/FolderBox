from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QSystemTrayIcon

from folderbox.startup import StartupError, is_startup_enabled, set_startup_enabled
from folderbox.window_manager import WindowManager


class TrayController:
    def __init__(self, app: QApplication, manager: WindowManager) -> None:
        self.app = app
        self.manager = manager
        self.tray = QSystemTrayIcon(app.windowIcon(), app)
        self.menu = QMenu()
        self.workspace_menu = self.menu.addMenu("工作区")
        self.delete_workspace_menu = self.menu.addMenu("删除工作区")

        self.toggle_action = QAction("隐藏 / 显示全部 Box", self.menu)
        self.new_box_action = QAction("新建 Box", self.menu)
        self.save_workspace_action = QAction("保存当前工作区…", self.menu)
        self.startup_action = QAction("开机启动", self.menu)
        self.startup_action.setCheckable(True)
        self.quit_action = QAction("退出 FolderBox", self.menu)

        self.menu.insertAction(self.workspace_menu.menuAction(), self.toggle_action)
        self.menu.insertAction(self.workspace_menu.menuAction(), self.new_box_action)
        self.menu.insertSeparator(self.workspace_menu.menuAction())
        self.workspace_menu.addAction(self.save_workspace_action)
        self.menu.addSeparator()
        self.menu.addAction(self.startup_action)
        self.menu.addAction(self.quit_action)

        self.toggle_action.triggered.connect(self.manager.toggle_all)
        self.new_box_action.triggered.connect(lambda: self.manager.open_new_window(None))
        self.save_workspace_action.triggered.connect(self.save_workspace)
        self.startup_action.triggered.connect(self.set_startup)
        self.quit_action.triggered.connect(self.manager.quit)
        self.menu.aboutToShow.connect(self.refresh_workspace_menus)
        self.tray.activated.connect(self._on_activated)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("FolderBox")

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self) -> None:
        self.refresh_workspace_menus()
        self.tray.show()

    def refresh_workspace_menus(self) -> None:
        self.startup_action.blockSignals(True)
        self.startup_action.setChecked(is_startup_enabled())
        self.startup_action.blockSignals(False)

        self.workspace_menu.clear()
        self.delete_workspace_menu.clear()
        self.workspace_menu.addAction(self.save_workspace_action)
        self.workspace_menu.addSeparator()

        names = self.manager.workspace_names()
        active = self.manager.active_workspace()
        if not names:
            empty_action = self.workspace_menu.addAction("暂无已保存工作区")
            empty_action.setEnabled(False)
            delete_empty = self.delete_workspace_menu.addAction("暂无已保存工作区")
            delete_empty.setEnabled(False)
            return

        for name in names:
            action = self.workspace_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(name == active)
            action.triggered.connect(lambda checked=False, value=name: self.load_workspace(value))

            delete_action = self.delete_workspace_menu.addAction(name)
            delete_action.triggered.connect(
                lambda checked=False, value=name: self.delete_workspace(value)
            )

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
        self.refresh_workspace_menus()

    def load_workspace(self, name: str) -> None:
        if not self.manager.load_workspace(name):
            QMessageBox.warning(None, "切换工作区失败", f"无法加载工作区：{name}")
        self.refresh_workspace_menus()

    def delete_workspace(self, name: str) -> None:
        reply = QMessageBox.question(
            None,
            "删除工作区",
            f"确定删除工作区“{name}”吗？\n不会删除磁盘中的任何文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.manager.delete_workspace(name)
        self.refresh_workspace_menus()

    def set_startup(self, enabled: bool) -> None:
        try:
            set_startup_enabled(enabled)
        except StartupError as exc:
            self.startup_action.blockSignals(True)
            self.startup_action.setChecked(is_startup_enabled())
            self.startup_action.blockSignals(False)
            QMessageBox.warning(None, "开机启动设置失败", str(exc))

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.manager.toggle_all()
