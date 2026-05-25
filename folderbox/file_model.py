from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Qt
from PySide6.QtWidgets import QFileSystemModel


class FolderFileModel:
    def __init__(self) -> None:
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.model.setNameFilterDisables(False)
        self.model.sort(0, Qt.AscendingOrder)
        self._root_path = ""

    def set_root_path(self, folder: str | Path) -> QModelIndex:
        path = str(Path(folder))
        self._root_path = path
        index = self.model.setRootPath(path)
        self.model.sort(0, Qt.AscendingOrder)
        return index

    def current_root_path(self) -> str:
        return self._root_path

    def root_index(self) -> QModelIndex:
        if not self._root_path:
            return QModelIndex()
        return self.model.index(self._root_path)

    def refresh_folder(self) -> QModelIndex:
        if not self._root_path:
            return QModelIndex()
        return self.set_root_path(self._root_path)

    def path_for_index(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        return self.model.filePath(index)

    def is_dir(self, index: QModelIndex) -> bool:
        return index.isValid() and self.model.isDir(index)

    def item_count(self) -> int:
        if not self._root_path:
            return 0
        directory = QDir(self._root_path)
        if not directory.exists():
            return 0
        entries = directory.entryList(QDir.AllEntries | QDir.NoDotAndDotDot, QDir.Name | QDir.IgnoreCase)
        return len(entries)
