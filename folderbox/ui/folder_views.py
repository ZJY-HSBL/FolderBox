from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, QModelIndex, Qt, QUrl
from PySide6.QtGui import QDrag, QDragEnterEvent, QDropEvent, QKeyEvent, QWheelEvent
from PySide6.QtWidgets import QAbstractItemView, QLabel, QListView, QTreeView

if TYPE_CHECKING:
    from folderbox.main_window import MainWindow


def local_file_mime_data(paths: list[str]) -> QMimeData:
    mime_data = QMimeData()
    urls = [QUrl.fromLocalFile(str(Path(path))) for path in paths if path]
    mime_data.setUrls(urls)
    return mime_data


class FolderDragDropMixin:
    window: MainWindow

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.window.handle_file_view_key(event, self):
            return
        super().keyPressEvent(event)

    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        paths = self.window.selected_paths()
        if not paths:
            return

        drag = QDrag(self)
        drag.setMimeData(local_file_mime_data(paths))

        index = self.currentIndex()
        if index.isValid():
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            if icon is not None and hasattr(icon, "pixmap"):
                drag.setPixmap(icon.pixmap(32, 32))

        drag.exec(
            Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
            Qt.DropAction.CopyAction,
        )

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


class DesktopListView(FolderDragDropMixin, QListView):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta:
                self.window.adjust_icon_size(8 if delta > 0 else -8)
            event.accept()
            return
        super().wheelEvent(event)


class DesktopTreeView(FolderDragDropMixin, QTreeView):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)


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
