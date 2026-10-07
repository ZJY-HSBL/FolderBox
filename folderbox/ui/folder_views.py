from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QLabel, QListView, QTreeView

if TYPE_CHECKING:
    from folderbox.main_window import MainWindow


class DesktopListView(QListView):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.window.handle_file_view_key(event, self):
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            position = event.position().toPoint()
            self.window.copy_dropped_files(event.mimeData(), self.indexAt(position))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class DesktopTreeView(QTreeView):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.window.handle_file_view_key(event, self):
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            position = event.position().toPoint()
            self.window.copy_dropped_files(event.mimeData(), self.indexAt(position))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class DropLabel(QLabel):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            self.window.copy_dropped_files(event.mimeData(), QModelIndex())
            event.acceptProposedAction()
        else:
            event.ignore()
