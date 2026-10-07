from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, QModelIndex, QUrl, Qt
from PySide6.QtGui import QDrag, QDragEnterEvent, QDropEvent, QIcon, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QLabel, QListView, QTreeView

if TYPE_CHECKING:
    from folderbox.main_window import MainWindow


def build_file_mime_data(paths: list[str]) -> QMimeData:
    mime_data = QMimeData()
    urls = [
        QUrl.fromLocalFile(str(path))
        for path in paths
        if Path(path).exists()
    ]
    mime_data.setUrls(urls)
    return mime_data


def start_file_drag(view: QAbstractItemView, window: MainWindow) -> None:
    paths = window.selected_paths()
    if not paths:
        return

    mime_data = build_file_mime_data(paths)
    if not mime_data.hasUrls():
        return

    drag = QDrag(view)
    drag.setMimeData(mime_data)

    index = view.currentIndex()
    if index.isValid():
        icon = view.model().data(index.siblingAtColumn(0), Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            drag.setPixmap(icon.pixmap(48, 48))

    drag.exec(
        Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
        Qt.DropAction.CopyAction,
    )


def accept_copy_drop(event: QDragEnterEvent | QDropEvent) -> None:
    event.setDropAction(Qt.DropAction.CopyAction)
    event.accept()


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

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        start_file_drag(self, self.window)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            accept_copy_drop(event)
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            accept_copy_drop(event)
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            position = event.position().toPoint()
            self.window.copy_dropped_files(event.mimeData(), self.indexAt(position))
            accept_copy_drop(event)
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

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        start_file_drag(self, self.window)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            accept_copy_drop(event)
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            accept_copy_drop(event)
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            position = event.position().toPoint()
            self.window.copy_dropped_files(event.mimeData(), self.indexAt(position))
            accept_copy_drop(event)
        else:
            super().dropEvent(event)


class DropLabel(QLabel):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            accept_copy_drop(event)
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self.window.can_accept_file_drop(event.mimeData()):
            self.window.copy_dropped_files(event.mimeData(), QModelIndex())
            accept_copy_drop(event)
        else:
            event.ignore()
