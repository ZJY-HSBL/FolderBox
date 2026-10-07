from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from folderbox.utils import format_exception


class TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class FunctionTask(QRunnable):
    def __init__(self, function: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.signals = TaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.function(*self.args)
        except Exception as exc:
            self.signals.failed.emit(format_exception(exc))
            return
        self.signals.finished.emit(result)
