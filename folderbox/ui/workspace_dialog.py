from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from folderbox.window_manager import WindowManager


class WorkspaceDialog(QDialog):
    def __init__(self, manager: WindowManager, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Workspace 管理")
        self.setMinimumSize(460, 340)

        layout = QVBoxLayout(self)
        description = QLabel("保存、切换和整理整套 FolderBox 桌面布局。")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.load_selected())
        layout.addWidget(self.list_widget, 1)

        primary_row = QHBoxLayout()
        self.load_button = QPushButton("切换")
        self.update_button = QPushButton("保存当前布局")
        self.save_as_button = QPushButton("另存为…")
        primary_row.addWidget(self.load_button)
        primary_row.addWidget(self.update_button)
        primary_row.addWidget(self.save_as_button)
        layout.addLayout(primary_row)

        secondary_row = QHBoxLayout()
        self.rename_button = QPushButton("重命名")
        self.delete_button = QPushButton("删除")
        self.close_button = QPushButton("关闭")
        secondary_row.addWidget(self.rename_button)
        secondary_row.addWidget(self.delete_button)
        secondary_row.addStretch(1)
        secondary_row.addWidget(self.close_button)
        layout.addLayout(secondary_row)

        self.load_button.clicked.connect(self.load_selected)
        self.update_button.clicked.connect(self.update_active)
        self.save_as_button.clicked.connect(self.save_as)
        self.rename_button.clicked.connect(self.rename_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.accept)
        self.list_widget.itemSelectionChanged.connect(self._sync_buttons)

        self.refresh()

    def refresh(self) -> None:
        selected = self.selected_name()
        active = self.manager.active_workspace()
        self.list_widget.clear()

        for name in self.manager.workspace_names():
            count = self.manager.workspace_box_count(name)
            suffix = " · 当前" if name == active else ""
            item = QListWidgetItem(f"{name}  ·  {count} 个 Box{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.list_widget.addItem(item)
            if name == selected:
                self.list_widget.setCurrentItem(item)

        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)
        self._sync_buttons()

    def selected_name(self) -> str:
        item = self.list_widget.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else ""

    def _sync_buttons(self) -> None:
        has_selection = bool(self.selected_name())
        self.load_button.setEnabled(has_selection)
        self.rename_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.update_button.setEnabled(bool(self.manager.active_workspace()))

    def load_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        if not self.manager.load_workspace(name):
            QMessageBox.warning(self, "切换失败", f"无法加载工作区：{name}")
        self.refresh()

    def update_active(self) -> None:
        name = self.manager.active_workspace()
        if not name:
            return
        try:
            self.manager.save_workspace(name)
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.refresh()

    def save_as(self) -> None:
        name, ok = QInputDialog.getText(self, "另存为 Workspace", "Workspace 名称：")
        clean_name = name.strip()
        if not ok or not clean_name:
            return
        if clean_name in self.manager.workspace_names():
            QMessageBox.warning(self, "保存失败", "已存在同名 Workspace；请换一个名称。")
            return
        try:
            self.manager.save_workspace(clean_name)
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.refresh()

    def rename_selected(self) -> None:
        old_name = self.selected_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(
            self,
            "重命名 Workspace",
            "新名称：",
            text=old_name,
        )
        if not ok or not new_name.strip():
            return
        if not self.manager.rename_workspace(old_name, new_name):
            QMessageBox.warning(self, "重命名失败", "名称无效或已存在同名 Workspace。")
            return
        self.refresh()

    def delete_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        reply = QMessageBox.question(
            self,
            "删除 Workspace",
            f"确定删除“{name}”吗？\n不会删除磁盘中的任何文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.manager.delete_workspace(name)
        self.refresh()
