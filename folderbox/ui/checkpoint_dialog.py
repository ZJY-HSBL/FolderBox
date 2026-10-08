from __future__ import annotations

from datetime import datetime
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


class WorkspaceCheckpointDialog(QDialog):
    def __init__(self, manager: WindowManager, workspace_name: str, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.workspace_name = workspace_name.strip()
        self.setWindowTitle(f"Workspace 恢复点 · {self.workspace_name}")
        self.setMinimumSize(520, 360)

        layout = QVBoxLayout(self)
        description = QLabel(
            "恢复点保存当前 Box 状态和自动布局策略，可用于回到一个稳定桌面状态。"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget, 1)

        action_row = QHBoxLayout()
        self.create_button = QPushButton("创建恢复点")
        self.restore_button = QPushButton("恢复")
        self.delete_button = QPushButton("删除")
        self.close_button = QPushButton("关闭")
        action_row.addWidget(self.create_button)
        action_row.addWidget(self.restore_button)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        action_row.addWidget(self.close_button)
        layout.addLayout(action_row)

        self.create_button.clicked.connect(self.create_checkpoint)
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.accept)
        self.list_widget.itemSelectionChanged.connect(self._sync_buttons)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.restore_selected())

        self.refresh()

    def refresh(self) -> None:
        selected_id = self.selected_checkpoint_id()
        self.list_widget.clear()

        for checkpoint in reversed(self.manager.workspace_checkpoints(self.workspace_name)):
            label = str(checkpoint["label"])
            created_at = str(checkpoint.get("created_at", "") or "")
            count = len(checkpoint.get("windows", []))
            layout_mode = str(checkpoint.get("layout_mode", "") or "")
            automatic = bool(checkpoint.get("automatic", False))
            suffix = f" · {count} 个 Box"
            if automatic:
                suffix += " · 自动安全"
            if layout_mode:
                suffix += f" · {layout_mode}"
            if created_at:
                suffix += f" · {created_at}"
            item = QListWidgetItem(f"{label}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, checkpoint["id"])
            self.list_widget.addItem(item)
            if checkpoint["id"] == selected_id:
                self.list_widget.setCurrentItem(item)

        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)
        self._sync_buttons()

    def selected_checkpoint_id(self) -> str:
        item = self.list_widget.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole) or "") if item else ""

    def _sync_buttons(self) -> None:
        has_selection = bool(self.selected_checkpoint_id())
        self.restore_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def create_checkpoint(self) -> None:
        default_label = datetime.now().strftime("Checkpoint %Y-%m-%d %H:%M")
        label, ok = QInputDialog.getText(
            self,
            "创建 Workspace 恢复点",
            "恢复点名称：",
            text=default_label,
        )
        if not ok or not label.strip():
            return
        try:
            checkpoint_id = self.manager.create_workspace_checkpoint(
                self.workspace_name,
                label,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "创建失败", str(exc))
            return

        self.refresh()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if str(item.data(Qt.ItemDataRole.UserRole) or "") == checkpoint_id:
                self.list_widget.setCurrentItem(item)
                break

    def restore_selected(self) -> None:
        checkpoint_id = self.selected_checkpoint_id()
        if not checkpoint_id:
            return
        reply = QMessageBox.question(
            self,
            "恢复 Workspace",
            "确定恢复到这个恢复点吗？当前 Workspace 状态会被替换。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if not self.manager.restore_workspace_checkpoint(
            self.workspace_name,
            checkpoint_id,
        ):
            QMessageBox.warning(self, "恢复失败", "无法恢复该 Workspace 恢复点。")
            return
        self.refresh()

    def delete_selected(self) -> None:
        checkpoint_id = self.selected_checkpoint_id()
        if not checkpoint_id:
            return
        reply = QMessageBox.question(
            self,
            "删除恢复点",
            "确定删除这个恢复点吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.manager.delete_workspace_checkpoint(
            self.workspace_name,
            checkpoint_id,
        )
        self.refresh()
