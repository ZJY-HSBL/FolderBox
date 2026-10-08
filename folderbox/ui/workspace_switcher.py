from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCursor, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from folderbox.window_manager import WindowManager


LAYOUT_LABELS = {
    "grid": "网格",
    "columns": "横向",
    "rows": "纵向",
    "cascade": "瀑布",
}


class WorkspaceSwitcher(QDialog):
    def __init__(self, manager: WindowManager, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("切换 Workspace")
        self.setMinimumWidth(420)
        self.resize(520, 360)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("切换 Workspace")
        title.setObjectName("switcherTitle")
        layout.addWidget(title)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("输入 Workspace 名称…")
        self.search_edit.setClearButtonEnabled(True)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget(self)
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget, 1)

        self.hint_label = QLabel("Enter 切换 · ↑↓ 选择 · Esc 关闭")
        self.hint_label.setObjectName("switcherHint")
        layout.addWidget(self.hint_label)

        self.search_edit.installEventFilter(self)
        self.search_edit.textChanged.connect(self._apply_filter)
        self.search_edit.returnPressed.connect(self.activate_selected)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.activate_selected())

    def show_switcher(self) -> None:
        self.refresh()
        self.search_edit.clear()
        self._center_on_pointer_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_edit.setFocus()

    def refresh(self) -> None:
        active = self.manager.active_workspace()
        selected = self.selected_name()
        self.list_widget.clear()

        for name in self.manager.workspace_names():
            count = self.manager.workspace_box_count(name)
            details = [f"{count} 个 Box"]
            layout_mode = self.manager.workspace_layout_mode(name)
            if layout_mode:
                details.append(LAYOUT_LABELS.get(layout_mode, layout_mode))
            hotkey_slot = self.manager.workspace_hotkey_slot(name)
            if hotkey_slot:
                details.append(f"Ctrl+Alt+{hotkey_slot}")

            prefix = "● " if name == active else "  "
            item = QListWidgetItem(f"{prefix}{name}    {' · '.join(details)}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.list_widget.addItem(item)
            if name == selected:
                self.list_widget.setCurrentItem(item)

        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)

    def selected_name(self) -> str:
        item = self.list_widget.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else ""

    def activate_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        if self.manager.load_workspace(name):
            self.accept()

    def _apply_filter(self, text: str) -> None:
        query = text.strip().casefold()
        first_visible: QListWidgetItem | None = None
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            name = str(item.data(Qt.ItemDataRole.UserRole) or "")
            visible = not query or query in name.casefold()
            item.setHidden(not visible)
            if visible and first_visible is None:
                first_visible = item

        current = self.list_widget.currentItem()
        if current is None or current.isHidden():
            self.list_widget.setCurrentItem(first_visible)

    def _center_on_pointer_screen(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        screen = app.screenAt(QCursor.pos()) or app.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        geometry = self.frameGeometry()
        geometry.moveCenter(available.center())
        self.move(geometry.topLeft())

    def eventFilter(self, watched, event) -> bool:
        if watched is self.search_edit and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.activate_selected()
                return True
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                self._move_selection(1 if key == Qt.Key.Key_Down else -1)
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.activate_selected()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self._move_selection(1 if event.key() == Qt.Key.Key_Down else -1)
            return
        super().keyPressEvent(event)

    def _move_selection(self, step: int) -> None:
        visible_rows = [
            index
            for index in range(self.list_widget.count())
            if not self.list_widget.item(index).isHidden()
        ]
        if not visible_rows:
            return

        current = self.list_widget.currentRow()
        if current not in visible_rows:
            target = visible_rows[0]
        else:
            position = visible_rows.index(current)
            target = visible_rows[(position + step) % len(visible_rows)]
        self.list_widget.setCurrentRow(target)
