from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget


class BreadcrumbBar(QWidget):
    pathSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_path(self, path: str) -> None:
        self._clear()
        if not path:
            placeholder = QLabel("未选择文件夹")
            self.layout.addWidget(placeholder)
            self.layout.addStretch(1)
            return

        parts = Path(path).parts
        if not parts:
            placeholder = QLabel(path)
            self.layout.addWidget(placeholder)
            self.layout.addStretch(1)
            return

        current = Path(parts[0])
        for index, part in enumerate(parts):
            if index > 0:
                current = current / part

            if index > 0:
                separator = QLabel("›")
                separator.setObjectName("breadcrumbSeparator")
                self.layout.addWidget(separator)

            button = QToolButton(self)
            label = part.rstrip("\\/") or part
            button.setText(label)
            button.setAutoRaise(True)
            button.setToolTip(str(current))
            button.clicked.connect(
                lambda checked=False, target=str(current): self.pathSelected.emit(target)
            )
            self.layout.addWidget(button)

        self.layout.addStretch(1)

    def _clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
