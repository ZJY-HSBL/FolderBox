from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QItemSelectionModel, QMimeData, QModelIndex, QPoint, QSize, QUrl, Qt
from PySide6.QtGui import (
    QCloseEvent,
    QDragEnterEvent,
    QDropEvent,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QSizeGrip,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from folderbox.config_manager import ConfigManager
from folderbox.file_model import FolderFileModel
from folderbox.file_ops import (
    FileOperationError,
    copy_items,
    delete_to_recycle_bin,
    open_folder_in_explorer,
    open_with_default_app,
    rename_item,
    show_in_explorer,
)
from folderbox.utils import format_exception, path_exists, shorten_path


TEXT = {
    "choose": "\u9009\u62e9\u6587\u4ef6\u5939",
    "back": "\u4e0a\u4e00\u7ea7",
    "refresh": "\u5237\u65b0",
    "pin": "\u7f6e\u9876",
    "new_window": "\u65b0\u7a97\u53e3",
    "view_icons": "\u56fe\u6807",
    "view_details": "\u8be6\u7ec6\u4fe1\u606f",
    "switch_to_icons": "\u5207\u6362\u5230\u56fe\u6807\u89c6\u56fe",
    "switch_to_details": "\u5207\u6362\u5230\u8be6\u7ec6\u4fe1\u606f",
    "minimize": "\u6700\u5c0f\u5316",
    "close": "\u5173\u95ed",
    "not_selected": "\u672a\u9009\u62e9\u6587\u4ef6\u5939",
    "select_hint": "\u8bf7\u9009\u62e9\u6587\u4ef6\u5939",
    "loaded": "\u5df2\u52a0\u8f7d\u6587\u4ef6\u5939",
    "entered": "\u5df2\u8fdb\u5165\u6587\u4ef6\u5939",
    "opened": "\u5df2\u6253\u5f00\u6587\u4ef6",
    "ready": "\u5c31\u7eea",
    "empty": "\u5f53\u524d\u6587\u4ef6\u5939\u4e3a\u7a7a\uff0c\u53ef\u4ee5\u62d6\u5165\u6587\u4ef6",
    "missing": "\u5f53\u524d\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\uff0c\u8bf7\u91cd\u65b0\u9009\u62e9\u6587\u4ef6\u5939",
    "open": "\u6253\u5f00",
    "copy": "\u590d\u5236",
    "paste": "\u7c98\u8d34",
    "rename": "\u91cd\u547d\u540d",
    "delete": "\u5220\u9664",
    "show": "\u5728\u8d44\u6e90\u7ba1\u7406\u5668\u4e2d\u663e\u793a",
    "open_folder": "\u5728\u8d44\u6e90\u7ba1\u7406\u5668\u4e2d\u6253\u5f00\u5f53\u524d\u6587\u4ef6\u5939",
    "confirm_delete": "\u786e\u8ba4\u5220\u9664",
    "delete_question": "\u786e\u5b9a\u5c06\u9009\u4e2d\u7684 {count} \u4e2a\u9879\u76ee\u79fb\u5165\u56de\u6536\u7ad9\u5417\uff1f",
    "new_name": "\u65b0\u540d\u79f0\uff1a",
    "opacity_tip": "\u80cc\u666f\u900f\u660e\u5ea6\uff08\u56fe\u6807\u548c\u6587\u5b57\u4fdd\u6301\u4e0d\u900f\u660e\uff09",
    "drop_copy": "\u5df2\u62d6\u5165\u590d\u5236 {count} \u4e2a\u9879\u76ee",
}


class DesktopListView(QListView):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.StandardKey.Copy):
            self.window.copy_selected()
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.window.paste_to_current_folder()
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.window.open_selected()
            return
        if event.key() == Qt.Key.Key_F2:
            self.window.rename_selected()
            return
        if event.key() == Qt.Key.Key_Delete:
            self.window.delete_selected()
            return
        if event.key() == Qt.Key.Key_Backspace:
            self.window.go_to_parent()
            return
        if event.key() == Qt.Key.Key_F5:
            self.window.refresh_current_folder()
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
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.StandardKey.Copy):
            self.window.copy_selected()
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.window.paste_to_current_folder()
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.window.open_selected()
            return
        if event.key() == Qt.Key.Key_F2:
            self.window.rename_selected()
            return
        if event.key() == Qt.Key.Key_Delete:
            self.window.delete_selected()
            return
        if event.key() == Qt.Key.Key_Backspace:
            self.window.go_to_parent()
            return
        if event.key() == Qt.Key.Key_F5:
            self.window.refresh_current_folder()
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
    def __init__(self, window: "MainWindow") -> None:
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


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: ConfigManager,
        manager: object | None = None,
        initial_state: dict[str, Any] | None = None,
        instance_offset: int = 0,
    ) -> None:
        super().__init__()
        self.config = config
        self.manager = manager
        self.initial_state = initial_state or {}
        self.instance_offset = instance_offset
        self.file_model = FolderFileModel()
        self.current_folder = ""
        self.copied_paths: list[str] = []
        self._drag_offset: QPoint | None = None
        self.background_opacity = self._initial_background_opacity()
        self.view_mode = self._initial_view_mode()

        self.setWindowTitle("FolderBox")
        self.setMinimumSize(320, 340)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._restore_window_state()
        self._build_ui()
        self._connect_model_signals()
        self._apply_background_opacity(int(self.background_opacity * 100))
        self._apply_always_on_top(bool(self.initial_state.get("always_on_top", self.config.get("always_on_top", False))), initial=True)

        last_folder = str(self.initial_state.get("folder", self.config.get("last_folder", "")) or "")
        if path_exists(last_folder) and Path(last_folder).is_dir():
            self.set_current_folder(last_folder, TEXT["loaded"])
        else:
            self.show_empty_state(TEXT["select_hint"])

    def _build_ui(self) -> None:
        outer = QWidget(self)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(8, 8, 8, 8)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        outer_layout.addWidget(self.shell)

        root_layout = QVBoxLayout(self.shell)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(8)

        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.mousePressEvent = self._title_mouse_press
        self.title_bar.mouseMoveEvent = self._title_mouse_move
        self.title_bar.mouseReleaseEvent = self._title_mouse_release
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)

        self.title_label = QLabel("FolderBox")
        self.title_label.setObjectName("titleLabel")
        self.path_label = QLabel(TEXT["not_selected"])
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.choose_button = QPushButton(TEXT["choose"])
        self.back_button = QToolButton()
        self.back_button.setText(TEXT["back"])
        self.refresh_button = QToolButton()
        self.refresh_button.setText(TEXT["refresh"])
        self.pin_button = QToolButton()
        self.pin_button.setText(TEXT["pin"])
        self.pin_button.setCheckable(True)
        self.new_window_button = QToolButton()
        self.new_window_button.setText(TEXT["new_window"])
        self.view_button = QToolButton()
        self.view_button.setToolTip(TEXT["switch_to_details"])
        self.min_button = QToolButton()
        self.min_button.setText("-")
        self.min_button.setToolTip(TEXT["minimize"])
        self.close_button = QToolButton()
        self.close_button.setText("x")
        self.close_button.setToolTip(TEXT["close"])

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setFixedWidth(74)
        self.opacity_slider.setToolTip(TEXT["opacity_tip"])
        self.opacity_slider.setValue(int(self.background_opacity * 100))

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.path_label, 1)
        title_layout.addWidget(self.choose_button)
        title_layout.addWidget(self.back_button)
        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.pin_button)
        title_layout.addWidget(self.new_window_button)
        title_layout.addWidget(self.view_button)
        title_layout.addWidget(self.opacity_slider)
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        root_layout.addWidget(self.title_bar)

        self.list_view = DesktopListView(self)
        self.list_view.setModel(self.file_model.model)
        self.list_view.setModelColumn(0)
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.setViewMode(QListView.ViewMode.IconMode)
        self.list_view.setMovement(QListView.Movement.Static)
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setFlow(QListView.Flow.LeftToRight)
        self.list_view.setWrapping(True)
        self.list_view.setWordWrap(True)
        self.list_view.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.list_view.setIconSize(QSize(40, 40))
        self.list_view.setGridSize(QSize(104, 92))
        self.list_view.setSpacing(8)
        self.list_view.setSelectionRectVisible(True)

        self.details_view = DesktopTreeView(self)
        self.details_view.setModel(self.file_model.model)
        self.details_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.details_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.details_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.details_view.setAlternatingRowColors(True)
        self.details_view.setRootIsDecorated(False)
        self.details_view.setItemsExpandable(False)
        self.details_view.setAllColumnsShowFocus(True)
        self.details_view.setSortingEnabled(True)
        self.details_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.details_view.header().setStretchLastSection(False)
        self.details_view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.details_view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.details_view.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.details_view.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.details_view.setColumnWidth(0, 230)
        self.details_view.setColumnWidth(1, 90)
        self.details_view.setColumnWidth(2, 120)
        self.details_view.setColumnWidth(3, 150)

        self.empty_label = DropLabel(self)
        self.empty_label.setText(TEXT["select_hint"])
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.empty_label.setObjectName("emptyLabel")

        self.stack = QStackedWidget()
        self.stack.addWidget(self.list_view)
        self.stack.addWidget(self.details_view)
        self.stack.addWidget(self.empty_label)
        root_layout.addWidget(self.stack, 1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel(TEXT["select_hint"])
        self.status_label.setObjectName("statusLabel")
        self.size_grip = QSizeGrip(self.shell)
        bottom_layout.addWidget(self.status_label, 1)
        bottom_layout.addWidget(self.size_grip)
        root_layout.addLayout(bottom_layout)

        self.setCentralWidget(outer)
        self._refresh_style_sheet()
        self._update_view_button_text()

        self.choose_button.clicked.connect(self.choose_folder)
        self.back_button.clicked.connect(self.go_to_parent)
        self.refresh_button.clicked.connect(self.refresh_current_folder)
        self.pin_button.toggled.connect(self._apply_always_on_top)
        self.new_window_button.clicked.connect(self.open_new_window)
        self.view_button.clicked.connect(self.toggle_view_mode)
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.close)
        self.opacity_slider.valueChanged.connect(self._apply_background_opacity)
        self.list_view.doubleClicked.connect(self.open_index)
        self.details_view.doubleClicked.connect(self.open_index)
        self.list_view.customContextMenuRequested.connect(lambda position: self.show_file_context_menu(position, self.list_view))
        self.details_view.customContextMenuRequested.connect(lambda position: self.show_file_context_menu(position, self.details_view))
        self.empty_label.customContextMenuRequested.connect(self.show_empty_context_menu)

    def _connect_model_signals(self) -> None:
        self.file_model.model.directoryLoaded.connect(self._on_directory_loaded)
        self.file_model.model.rowsInserted.connect(lambda *_: self.update_folder_state())
        self.file_model.model.rowsRemoved.connect(lambda *_: self.update_folder_state())
        self.file_model.model.layoutChanged.connect(lambda *_: self.update_folder_state())

    def _restore_window_state(self) -> None:
        x = int(self.initial_state.get("x", self.config.get("window_x", 200)) or 200)
        y = int(self.initial_state.get("y", self.config.get("window_y", 200)) or 200)
        width = max(320, int(self.initial_state.get("width", self.config.get("window_width", 420)) or 420))
        height = max(340, int(self.initial_state.get("height", self.config.get("window_height", 520)) or 520))
        if not self.initial_state and self.instance_offset:
            x += self.instance_offset * 36
            y += self.instance_offset * 36
        self.setGeometry(x, y, width, height)

    def _initial_background_opacity(self) -> float:
        raw_value = self.initial_state.get(
            "background_opacity",
            self.config.get("background_opacity", self.config.get("window_opacity", 0.72)),
        )
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = 0.72
        return max(0.2, min(1.0, value))

    def _initial_view_mode(self) -> str:
        value = str(self.initial_state.get("view_mode", self.config.get("view_mode", "icons")) or "icons")
        return value if value in {"icons", "details"} else "icons"

    def _apply_background_opacity(self, value: int) -> None:
        self.background_opacity = max(0.2, min(1.0, value / 100))
        self.config.set("background_opacity", round(self.background_opacity, 2))
        self.config.set("window_opacity", round(self.background_opacity, 2))
        if hasattr(self, "shell"):
            self._refresh_style_sheet()

    def _refresh_style_sheet(self) -> None:
        shell_alpha = int(255 * self.background_opacity)
        list_alpha = int(145 * self.background_opacity)
        hover_alpha = int(130 * self.background_opacity)
        button_alpha = int(180 * self.background_opacity)
        button_hover_alpha = int(225 * self.background_opacity)
        border_alpha = max(90, int(190 * self.background_opacity))
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: transparent; }}
            QFrame#shell {{
                background: rgba(244, 247, 250, {shell_alpha});
                border: 1px solid rgba(122, 132, 145, {border_alpha});
                border-radius: 10px;
            }}
            QWidget#titleBar {{ background: transparent; }}
            QLabel#titleLabel {{ font-weight: 700; color: #111827; }}
            QLabel#statusLabel, QLabel#emptyLabel, QLabel {{ color: #1f2937; }}
            QLabel#emptyLabel {{ font-size: 14px; }}
            QListView, QTreeView {{
                background: rgba(255, 255, 255, {list_alpha});
                border: 1px solid rgba(130, 143, 158, {border_alpha});
                border-radius: 8px;
                padding: 8px;
                outline: none;
            }}
            QListView::item, QTreeView::item {{
                color: #111827;
                padding: 6px;
                border-radius: 7px;
            }}
            QListView::item:hover, QTreeView::item:hover {{ background: rgba(255, 255, 255, {hover_alpha}); }}
            QListView::item:selected, QTreeView::item:selected {{
                background: rgba(59, 130, 246, 130);
                color: #0f172a;
            }}
            QHeaderView::section {{
                background: rgba(255, 255, 255, {button_alpha});
                color: #111827;
                border: 0;
                border-right: 1px solid rgba(130, 143, 158, {border_alpha});
                padding: 5px 7px;
            }}
            QPushButton, QToolButton {{
                min-height: 24px;
                padding: 3px 8px;
                border: 1px solid rgba(107, 114, 128, {border_alpha});
                border-radius: 6px;
                background: rgba(255, 255, 255, {button_alpha});
                color: #111827;
            }}
            QPushButton:hover, QToolButton:hover {{ background: rgba(255, 255, 255, {button_hover_alpha}); }}
            QToolButton:checked {{ background: rgba(96, 165, 250, 170); border-color: rgba(37, 99, 235, 180); }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: rgba(31, 41, 55, 100);
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
                background: rgba(17, 24, 39, 230);
            }}
            QMenu {{
                background: rgba(255, 255, 255, 245);
                border: 1px solid rgba(148, 163, 184, 190);
            }}
            QMenu::item {{ padding: 5px 24px 5px 18px; color: #111827; }}
            QMenu::item:selected {{ background: rgba(219, 234, 254, 240); }}
            """
        )

    def _apply_always_on_top(self, enabled: bool, initial: bool = False) -> None:
        if hasattr(self, "pin_button"):
            self.pin_button.setChecked(enabled)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if not initial:
            self.show()
        self.config.set("always_on_top", enabled)
        if self.manager and not initial and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def set_current_folder(self, folder: str | Path, message: str = "") -> None:
        path = Path(folder)
        if not path.exists() or not path.is_dir():
            self.current_folder = ""
            self.config.set("last_folder", "")
            self.show_empty_state(TEXT["select_hint"])
            return

        self.current_folder = str(path)
        root_index = self.file_model.set_root_path(path)
        self.list_view.setRootIndex(root_index)
        self.details_view.setRootIndex(root_index)
        self._show_current_file_view()
        self.config.set("last_folder", self.current_folder)
        self.update_path_label()
        self.update_parent_button()
        self.update_folder_state(message or TEXT["loaded"])
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def show_empty_state(self, message: str) -> None:
        self.current_folder = ""
        self.path_label.setText(TEXT["not_selected"])
        self.path_label.setToolTip("")
        self.empty_label.setText(message)
        self.stack.setCurrentWidget(self.empty_label)
        self.back_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.status_label.setText(message)
        self.setWindowTitle("FolderBox")

    def update_path_label(self) -> None:
        if not self.current_folder:
            self.path_label.setText(TEXT["not_selected"])
            self.path_label.setToolTip("")
            return
        char_width = max(1, self.path_label.fontMetrics().averageCharWidth())
        available_width = max(24, self.path_label.width() // char_width)
        text = shorten_path(self.current_folder, min(96, max(32, available_width)))
        self.path_label.setText(text)
        self.path_label.setToolTip(self.current_folder)
        self.setWindowTitle(f"FolderBox - {Path(self.current_folder).name or self.current_folder}")

    def update_parent_button(self) -> None:
        if not self.current_folder:
            self.back_button.setEnabled(False)
            return
        current = Path(self.current_folder)
        self.back_button.setEnabled(current.parent != current and current.parent.exists())
        self.refresh_button.setEnabled(True)

    def update_folder_state(self, message: str | None = None) -> None:
        if not self.current_folder:
            self.show_empty_state(TEXT["select_hint"])
            return
        count = self.file_model.item_count()
        if count == 0:
            self.empty_label.setText(TEXT["empty"])
            self.stack.setCurrentWidget(self.empty_label)
        else:
            self._show_current_file_view()
        text = message or TEXT["ready"]
        self.status_label.setText(f"{count} \u4e2a\u9879\u76ee / {text}")
        self.update_parent_button()

    def selected_paths(self) -> list[str]:
        view = self.active_file_view()
        selection_model = view.selectionModel()
        if selection_model is None:
            return []
        paths: list[str] = []
        for index in selection_model.selectedRows(0):
            path = self.file_model.path_for_index(index.siblingAtColumn(0))
            if path:
                paths.append(path)
        return paths

    def active_file_view(self) -> QAbstractItemView:
        return self.details_view if self.view_mode == "details" else self.list_view

    def _show_current_file_view(self) -> None:
        self._update_view_button_text()
        if self.view_mode == "details":
            self.stack.setCurrentWidget(self.details_view)
        else:
            self.stack.setCurrentWidget(self.list_view)

    def _update_view_button_text(self) -> None:
        if self.view_mode == "details":
            self.view_button.setText(TEXT["view_details"])
            self.view_button.setToolTip(TEXT["switch_to_icons"])
        else:
            self.view_button.setText(TEXT["view_icons"])
            self.view_button.setToolTip(TEXT["switch_to_details"])

    def toggle_view_mode(self) -> None:
        self.set_view_mode("details" if self.view_mode == "icons" else "icons")

    def set_view_mode(self, mode: str) -> None:
        if mode not in {"icons", "details"}:
            return
        self.view_mode = mode
        self.config.set("view_mode", mode)
        self._update_view_button_text()
        if self.current_folder:
            self.update_folder_state()
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def clipboard_paths(self) -> list[str]:
        mime_data = QApplication.clipboard().mimeData()
        if not mime_data or not mime_data.hasUrls():
            return []
        paths: list[str] = []
        for url in mime_data.urls():
            if url.isLocalFile():
                local_path = url.toLocalFile()
                if path_exists(local_path):
                    paths.append(local_path)
        return paths

    def has_paste_data(self) -> bool:
        return bool(self.copied_paths or self.clipboard_paths())

    def can_accept_file_drop(self, mime_data: QMimeData) -> bool:
        return bool(self.current_folder and mime_data and mime_data.hasUrls())

    def _paths_from_mime_data(self, mime_data: QMimeData) -> list[str]:
        paths: list[str] = []
        for url in mime_data.urls():
            if url.isLocalFile():
                local_path = url.toLocalFile()
                if path_exists(local_path):
                    paths.append(local_path)
        return paths

    def choose_folder(self) -> None:
        start_dir = self.current_folder if path_exists(self.current_folder) else str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, TEXT["choose"], start_dir)
        if folder:
            self.set_current_folder(folder, TEXT["loaded"])

    def open_new_window(self) -> None:
        if self.manager and hasattr(self.manager, "open_new_window"):
            self.manager.open_new_window()
            return
        window = MainWindow(self.config, initial_state={"background_opacity": self.background_opacity}, instance_offset=1)
        window.show()

    def open_index(self, index: QModelIndex) -> None:
        index = index.siblingAtColumn(0)
        path = self.file_model.path_for_index(index)
        if not path:
            return
        if Path(path).is_dir():
            self.set_current_folder(path, TEXT["entered"])
            return
        try:
            open_with_default_app(path)
            self.update_folder_state(TEXT["opened"])
        except FileOperationError as exc:
            self.show_error("\u6253\u5f00\u5931\u8d25", str(exc))

    def open_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        first = paths[0]
        if Path(first).is_dir():
            self.set_current_folder(first, TEXT["entered"])
        else:
            try:
                open_with_default_app(first)
                self.update_folder_state(TEXT["opened"])
            except FileOperationError as exc:
                self.show_error("\u6253\u5f00\u5931\u8d25", str(exc))

    def go_to_parent(self) -> None:
        if not self.current_folder:
            return
        current = Path(self.current_folder)
        parent = current.parent
        if parent != current and parent.exists():
            self.set_current_folder(parent, "\u5df2\u8fd4\u56de\u4e0a\u4e00\u7ea7")

    def refresh_current_folder(self) -> None:
        if not self.current_folder:
            return
        if not path_exists(self.current_folder):
            self.config.set("last_folder", "")
            self.show_empty_state(TEXT["missing"])
            return
        root_index = self.file_model.refresh_folder()
        self.list_view.setRootIndex(root_index)
        self.details_view.setRootIndex(root_index)
        self.update_path_label()
        self.update_folder_state("\u5df2\u5237\u65b0")

    def copy_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        self.copied_paths = paths
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
        QApplication.clipboard().setMimeData(mime_data)
        self.update_folder_state(f"\u5df2\u590d\u5236 {len(paths)} \u4e2a\u9879\u76ee")

    def paste_to_current_folder(self) -> None:
        if not self.current_folder:
            return
        paths = self.copied_paths or self.clipboard_paths()
        if not paths:
            return
        self._copy_paths_to_folder(paths, self.current_folder, "\u7c98\u8d34")

    def copy_dropped_files(self, mime_data: QMimeData, target_index: QModelIndex) -> None:
        if not self.current_folder:
            return
        paths = self._paths_from_mime_data(mime_data)
        if not paths:
            return

        destination = self.current_folder
        if target_index.isValid():
            target_index = target_index.siblingAtColumn(0)
            target_path = self.file_model.path_for_index(target_index)
            if target_path and Path(target_path).is_dir():
                destination = target_path
        self._copy_paths_to_folder(paths, destination, "\u62d6\u5165\u590d\u5236")

    def _copy_paths_to_folder(self, paths: list[str], destination: str, action_name: str) -> None:
        try:
            copied, failures = copy_items(paths, destination)
        except FileOperationError as exc:
            self.show_error(f"{action_name}\u5931\u8d25", str(exc))
            return

        self.refresh_current_folder()
        if failures:
            details = "\n".join(f"{path.name}: {error}" for path, error in failures[:8])
            if len(failures) > 8:
                details += f"\n\u5176\u4f59 {len(failures) - 8} \u9879\u5931\u8d25\u3002"
            self.show_error(f"\u90e8\u5206\u9879\u76ee{action_name}\u5931\u8d25", details)
            self.update_folder_state(
                f"\u5df2{action_name} {len(copied)} \u4e2a\u9879\u76ee\uff0c{len(failures)} \u4e2a\u5931\u8d25"
            )
        else:
            self.update_folder_state(f"{action_name}\u5b8c\u6210\uff0c\u5171 {len(copied)} \u4e2a\u9879\u76ee")

    def delete_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return

        reply = QMessageBox.question(
            self,
            TEXT["confirm_delete"],
            TEXT["delete_question"].format(count=len(paths)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        failures = delete_to_recycle_bin(paths)
        self.refresh_current_folder()
        if failures:
            details = "\n".join(f"{path.name}: {error}" for path, error in failures[:8])
            self.show_error("\u90e8\u5206\u9879\u76ee\u5220\u9664\u5931\u8d25", details)
            self.update_folder_state(f"\u5220\u9664\u5b8c\u6210\uff0c{len(failures)} \u4e2a\u5931\u8d25")
        else:
            self.update_folder_state("\u5220\u9664\u5b8c\u6210")

    def rename_selected(self) -> None:
        paths = self.selected_paths()
        if len(paths) != 1:
            return
        source = Path(paths[0])
        new_name, ok = QInputDialog.getText(self, TEXT["rename"], TEXT["new_name"], text=source.name)
        if not ok:
            return
        try:
            rename_item(source, new_name)
            self.refresh_current_folder()
            self.update_folder_state("\u91cd\u547d\u540d\u5b8c\u6210")
        except FileOperationError as exc:
            self.show_error("\u91cd\u547d\u540d\u5931\u8d25", str(exc))

    def show_selected_in_explorer(self) -> None:
        paths = self.selected_paths()
        target = paths[0] if paths else self.current_folder
        if not target:
            return
        try:
            show_in_explorer(target)
        except FileOperationError as exc:
            self.show_error("\u8d44\u6e90\u7ba1\u7406\u5668", str(exc))

    def open_current_folder_in_explorer(self) -> None:
        if not self.current_folder:
            return
        try:
            open_folder_in_explorer(self.current_folder)
        except FileOperationError as exc:
            self.show_error("\u8d44\u6e90\u7ba1\u7406\u5668", str(exc))

    def show_file_context_menu(self, position: QPoint, view: QAbstractItemView) -> None:
        if view is self.details_view:
            self.view_mode = "details"
        else:
            self.view_mode = "icons"
        index = view.indexAt(position)
        if not index.isValid():
            self.show_empty_context_menu(view.viewport().mapToGlobal(position), is_global=True)
            return
        index = index.siblingAtColumn(0)

        selection_model = view.selectionModel()
        if selection_model and not selection_model.isSelected(index):
            selection_model.clearSelection()
            selection_model.select(
                index,
                QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
            )
            view.setCurrentIndex(index)

        menu = QMenu(self)
        open_action = menu.addAction(TEXT["open"])
        copy_action = menu.addAction(TEXT["copy"])
        rename_action = menu.addAction(TEXT["rename"])
        delete_action = menu.addAction(TEXT["delete"])
        show_action = menu.addAction(TEXT["show"])
        menu.addSeparator()
        refresh_action = menu.addAction(TEXT["refresh"])
        new_window_action = menu.addAction(TEXT["new_window"])
        view_action = menu.addAction(TEXT["switch_to_details"] if self.view_mode == "icons" else TEXT["switch_to_icons"])

        rename_action.setEnabled(len(self.selected_paths()) == 1)

        selected_action = menu.exec(view.viewport().mapToGlobal(position))
        if selected_action == open_action:
            self.open_selected()
        elif selected_action == copy_action:
            self.copy_selected()
        elif selected_action == rename_action:
            self.rename_selected()
        elif selected_action == delete_action:
            self.delete_selected()
        elif selected_action == show_action:
            self.show_selected_in_explorer()
        elif selected_action == refresh_action:
            self.refresh_current_folder()
        elif selected_action == new_window_action:
            self.open_new_window()
        elif selected_action == view_action:
            self.toggle_view_mode()

    def show_empty_context_menu(self, position: QPoint, is_global: bool = False) -> None:
        global_position = position if is_global else self.empty_label.mapToGlobal(position)

        menu = QMenu(self)
        if self.current_folder:
            paste_action = menu.addAction(TEXT["paste"])
            paste_action.setEnabled(self.has_paste_data())
            refresh_action = menu.addAction(TEXT["refresh"])
            choose_action = menu.addAction(TEXT["choose"])
            new_window_action = menu.addAction(TEXT["new_window"])
            view_action = menu.addAction(TEXT["switch_to_details"] if self.view_mode == "icons" else TEXT["switch_to_icons"])
            open_folder_action = menu.addAction(TEXT["open_folder"])
        else:
            paste_action = None
            refresh_action = None
            open_folder_action = None
            view_action = None
            new_window_action = menu.addAction(TEXT["new_window"])
            choose_action = menu.addAction(TEXT["choose"])

        selected_action = menu.exec(global_position)
        if self.current_folder and selected_action == paste_action:
            self.paste_to_current_folder()
        elif self.current_folder and selected_action == refresh_action:
            self.refresh_current_folder()
        elif selected_action == choose_action:
            self.choose_folder()
        elif selected_action == new_window_action:
            self.open_new_window()
        elif view_action is not None and selected_action == view_action:
            self.toggle_view_mode()
        elif self.current_folder and selected_action == open_folder_action:
            self.open_current_folder_in_explorer()

    def snapshot_state(self) -> dict[str, Any]:
        geometry = self.geometry()
        return {
            "folder": self.current_folder if path_exists(self.current_folder) else "",
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
            "always_on_top": self.pin_button.isChecked(),
            "background_opacity": round(self.background_opacity, 2),
            "view_mode": self.view_mode,
        }

    def _on_directory_loaded(self, loaded_path: str) -> None:
        if self.current_folder and Path(loaded_path) == Path(self.current_folder):
            self.update_folder_state(TEXT["loaded"])

    def _title_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_mouse_move(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def _title_mouse_release(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        event.accept()

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.update_path_label()

    def closeEvent(self, event: QCloseEvent) -> None:
        state = self.snapshot_state()
        self.config.update(
            {
                "last_folder": state["folder"],
                "window_x": state["x"],
                "window_y": state["y"],
                "window_width": state["width"],
                "window_height": state["height"],
                "always_on_top": state["always_on_top"],
                "background_opacity": state["background_opacity"],
                "window_opacity": state["background_opacity"],
            }
        )
        try:
            if self.manager and hasattr(self.manager, "unregister_window"):
                self.manager.unregister_window(self)
            else:
                self.config.set("windows", [state])
                self.config.save()
        except Exception as exc:
            QMessageBox.warning(self, "\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25", format_exception(exc))
        event.accept()
