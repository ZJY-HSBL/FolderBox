from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    QThreadPool,
    QUrl,
    Qt,
    Slot,
)
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColorDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QHeaderView,
    QSizeGrip,
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from folderbox.config_manager import ConfigManager
from folderbox.file_model import FolderFileModel
from folderbox.file_ops import (
    FileOperationError,
    copy_items,
    create_folder,
    delete_to_recycle_bin,
    move_items,
    open_folder_in_explorer,
    open_with_default_app,
    rename_item,
    show_in_explorer,
)
from folderbox.tasks import FunctionTask
from folderbox.ui.breadcrumb import BreadcrumbBar
from folderbox.ui.folder_views import DesktopListView, DesktopTreeView, DropLabel
from folderbox.ui.theme import (
    DEFAULT_ACCENT_COLOR,
    build_stylesheet,
    normalize_accent_color,
    normalize_theme_mode,
)
from folderbox.utils import format_exception, path_exists


FOLDERBOX_CLIPBOARD_ACTION = "application/x-folderbox-action"


TEXT = {
    "choose": "\u9009\u62e9\u6587\u4ef6\u5939",
    "back": "后退",
    "forward": "前进",
    "up": "上一级",
    "refresh": "\u5237\u65b0",
    "pin": "置顶",
    "lock": "锁定",
    "unlock": "解锁",
    "lock_tip": "锁定位置和大小",
    "rename_box": "重命名 Box",
    "box_name": "Box 名称：",
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
    "copy": "复制",
    "cut": "剪切",
    "paste": "\u7c98\u8d34",
    "rename": "\u91cd\u547d\u540d",
    "delete": "\u5220\u9664",
    "show": "\u5728\u8d44\u6e90\u7ba1\u7406\u5668\u4e2d\u663e\u793a",
    "open_folder": "\u5728\u8d44\u6e90\u7ba1\u7406\u5668\u4e2d\u6253\u5f00\u5f53\u524d\u6587\u4ef6\u5939",
    "confirm_delete": "\u786e\u8ba4\u5220\u9664",
    "delete_question": "\u786e\u5b9a\u5c06\u9009\u4e2d\u7684 {count} \u4e2a\u9879\u76ee\u79fb\u5165\u56de\u6536\u7ad9\u5417\uff1f",
    "new_name": "新名称：",
    "new_folder": "新建文件夹",
    "folder_name": "文件夹名称：",
    "opacity_tip": "\u80cc\u666f\u900f\u660e\u5ea6\uff08\u56fe\u6807\u548c\u6587\u5b57\u4fdd\u6301\u4e0d\u900f\u660e\uff09",
    "drop_copy": "\u5df2\u62d6\u5165\u590d\u5236 {count} \u4e2a\u9879\u76ee",
}


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
        self._history: list[str] = []
        self._history_index = -1
        self.thread_pool = QThreadPool.globalInstance()
        self._file_task: FunctionTask | None = None
        self._file_task_action = ""
        self._file_task_on_finished: Callable[[object], None] | None = None
        self._drag_offset: QPoint | None = None
        self.background_opacity = self._initial_background_opacity()
        self.view_mode = self._initial_view_mode()
        self.box_title = str(self.initial_state.get("box_title", "") or "").strip()
        self.locked = bool(self.initial_state.get("locked", False))
        self.always_on_top = bool(self.initial_state.get("always_on_top", False))
        self.theme_mode = normalize_theme_mode(
            str(self.initial_state.get("theme_mode", "light") or "light")
        )
        self.accent_color = normalize_accent_color(
            str(self.initial_state.get("accent_color", DEFAULT_ACCENT_COLOR) or DEFAULT_ACCENT_COLOR)
        )
        self.icon_size = self._initial_icon_size()

        self.setWindowTitle("FolderBox")
        self.setMinimumSize(320, 340)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._restore_window_state()
        self._build_ui()
        self._connect_model_signals()
        self._apply_background_opacity(int(self.background_opacity * 100))
        self._apply_always_on_top(self.always_on_top, initial=True)
        self._apply_locked(self.locked, initial=True)

        last_folder = str(self.initial_state.get("folder", "") or "")
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

        self.title_label = QLabel(self.box_title or "FolderBox")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setToolTip("双击修改 Box 名称")
        self.title_label.mouseDoubleClickEvent = self._title_label_double_click

        style = self.style()

        self.choose_button = QToolButton()
        self.choose_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.choose_button.setToolTip(TEXT["choose"])
        self.back_button = QToolButton()
        self.back_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.back_button.setToolTip(TEXT["back"])
        self.forward_button = QToolButton()
        self.forward_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.forward_button.setToolTip(TEXT["forward"])
        self.up_button = QToolButton()
        self.up_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.up_button.setToolTip(TEXT["up"])
        self.refresh_button = QToolButton()
        self.refresh_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.setToolTip(TEXT["refresh"])
        self.view_button = QToolButton()
        self.view_button.setToolTip(TEXT["switch_to_details"])
        self.more_button = QToolButton()
        self.more_button.setText("⋯")
        self.more_button.setToolTip("更多")
        self.more_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.min_button = QToolButton()
        self.min_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton))
        self.min_button.setToolTip(TEXT["minimize"])
        self.close_button = QToolButton()
        self.close_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.close_button.setToolTip(TEXT["close"])

        for button in (self.more_button, self.min_button, self.close_button):
            button.setObjectName("windowControl")
            button.setAutoRaise(True)

        self._build_more_menu()
        self.more_button.setMenu(self.more_menu)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.more_button)
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        root_layout.addWidget(self.title_bar)

        self.navigation_bar = QWidget()
        self.navigation_bar.setObjectName("navigationBar")
        navigation_layout = QHBoxLayout(self.navigation_bar)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(5)

        self.breadcrumb = BreadcrumbBar(self.navigation_bar)
        self.search_edit = QLineEdit(self.navigation_bar)
        self.search_edit.setPlaceholderText("筛选当前文件夹…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMaximumWidth(190)
        self.search_edit.setToolTip("输入文件名进行快速过滤；支持 * 和 ? 通配符")

        navigation_layout.addWidget(self.choose_button)
        navigation_layout.addWidget(self.back_button)
        navigation_layout.addWidget(self.forward_button)
        navigation_layout.addWidget(self.up_button)
        navigation_layout.addWidget(self.breadcrumb, 1)
        navigation_layout.addWidget(self.search_edit)
        navigation_layout.addWidget(self.refresh_button)
        navigation_layout.addWidget(self.view_button)
        root_layout.addWidget(self.navigation_bar)

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
        self.list_view.setIconSize(QSize(self.icon_size, self.icon_size))
        self.list_view.setGridSize(self._icon_grid_size())
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
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.up_button.clicked.connect(self.go_to_parent)
        self.refresh_button.clicked.connect(self.refresh_current_folder)
        self.breadcrumb.pathSelected.connect(
            lambda path: self.set_current_folder(path, TEXT["entered"])
        )
        self.search_edit.textChanged.connect(self.apply_search_filter)
        self.view_button.clicked.connect(self.toggle_view_mode)
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.close)
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
        x = int(self.initial_state.get("x", 200) or 200)
        y = int(self.initial_state.get("y", 200) or 200)
        width = max(320, int(self.initial_state.get("width", 420) or 420))
        height = max(340, int(self.initial_state.get("height", 520) or 520))
        if not self.initial_state and self.instance_offset:
            x += self.instance_offset * 36
            y += self.instance_offset * 36
        geometry = QRect(x, y, width, height)
        screens = QApplication.screens()
        if screens and not any(screen.availableGeometry().intersects(geometry) for screen in screens):
            primary = QApplication.primaryScreen()
            if primary is not None:
                available = primary.availableGeometry()
                x = available.left() + 40
                y = available.top() + 40
        self.setGeometry(x, y, width, height)

    def _initial_background_opacity(self) -> float:
        raw_value = self.initial_state.get("background_opacity", 0.72)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = 0.72
        return max(0.2, min(1.0, value))

    def _initial_view_mode(self) -> str:
        value = str(self.initial_state.get("view_mode", "icons") or "icons")
        return value if value in {"icons", "details"} else "icons"

    def _initial_icon_size(self) -> int:
        try:
            value = int(self.initial_state.get("icon_size", 40) or 40)
        except (TypeError, ValueError):
            value = 40
        return min((32, 40, 48, 56), key=lambda size: abs(size - value))

    def _icon_grid_size(self) -> QSize:
        return QSize(self.icon_size * 2 + 24, self.icon_size + 52)

    def _apply_background_opacity(self, value: int) -> None:
        self.background_opacity = max(0.2, min(1.0, value / 100))
        if hasattr(self, "shell"):
            self._refresh_style_sheet()

    def _refresh_style_sheet(self) -> None:
        self.setStyleSheet(
            build_stylesheet(
                self.background_opacity,
                self.accent_color,
                self.theme_mode,
            )
        )

    def _apply_always_on_top(self, enabled: bool, initial: bool = False) -> None:
        self.always_on_top = enabled
        if hasattr(self, "pin_action"):
            self.pin_action.blockSignals(True)
            self.pin_action.setChecked(enabled)
            self.pin_action.blockSignals(False)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if not initial:
            self.show()
        if self.manager and not initial and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def _apply_locked(self, enabled: bool, initial: bool = False) -> None:
        self.locked = enabled
        if hasattr(self, "lock_action"):
            self.lock_action.blockSignals(True)
            self.lock_action.setChecked(enabled)
            self.lock_action.blockSignals(False)
        if hasattr(self, "size_grip"):
            self.size_grip.setVisible(not enabled)
            self.size_grip.setEnabled(not enabled)
        if not initial and self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def _build_more_menu(self) -> None:
        self.more_menu = QMenu(self)

        new_box_action = self.more_menu.addAction("新建 Box")
        rename_box_action = self.more_menu.addAction(TEXT["rename_box"])
        self.more_menu.addSeparator()

        self.pin_action = self.more_menu.addAction("保持置顶")
        self.pin_action.setCheckable(True)
        self.pin_action.setChecked(self.always_on_top)
        self.lock_action = self.more_menu.addAction("锁定位置和大小")
        self.lock_action.setCheckable(True)
        self.lock_action.setChecked(self.locked)

        self.more_menu.addSeparator()
        self.view_action = self.more_menu.addAction(TEXT["switch_to_details"])
        appearance_menu = self.more_menu.addMenu("外观")

        theme_menu = appearance_menu.addMenu("主题")
        self.theme_actions = {}
        for mode, label in (("light", "浅色"), ("dark", "深色")):
            action = theme_menu.addAction(label)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, value=mode: self._apply_theme_mode(value)
            )
            self.theme_actions[mode] = action

        accent_menu = appearance_menu.addMenu("强调色")
        self.accent_actions = {}
        for label, color in (
            ("蓝色", "#3b82f6"),
            ("紫色", "#8b5cf6"),
            ("青色", "#06b6d4"),
            ("绿色", "#22c55e"),
            ("橙色", "#f97316"),
            ("红色", "#ef4444"),
        ):
            action = accent_menu.addAction(label)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, value=color: self._apply_accent_color(value)
            )
            self.accent_actions[color] = action
        accent_menu.addSeparator()
        custom_accent_action = accent_menu.addAction("自定义…")

        icon_size_menu = appearance_menu.addMenu("图标大小")
        self.icon_size_actions = {}
        for size, label in ((32, "小"), (40, "中"), (48, "大"), (56, "超大")):
            action = icon_size_menu.addAction(f"{label} · {size}px")
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, value=size: self._apply_icon_size(value)
            )
            self.icon_size_actions[size] = action

        opacity_menu = appearance_menu.addMenu("背景透明度")
        for percent in (40, 60, 80, 100):
            action = opacity_menu.addAction(f"{percent}%")
            action.triggered.connect(
                lambda checked=False, value=percent: self._apply_background_opacity(value)
            )
        opacity_menu.addSeparator()
        custom_opacity_action = opacity_menu.addAction("自定义…")

        self.more_menu.addSeparator()
        self.open_folder_action = self.more_menu.addAction(TEXT["open_folder"])
        choose_folder_action = self.more_menu.addAction(TEXT["choose"])
        self.more_menu.aboutToShow.connect(self._sync_more_menu)

        new_box_action.triggered.connect(self.open_new_window)
        rename_box_action.triggered.connect(self.rename_box)
        self.pin_action.toggled.connect(self._apply_always_on_top)
        self.lock_action.toggled.connect(self._apply_locked)
        self.view_action.triggered.connect(self.toggle_view_mode)
        custom_accent_action.triggered.connect(self.choose_accent_color)
        custom_opacity_action.triggered.connect(self.choose_background_opacity)
        self.open_folder_action.triggered.connect(self.open_current_folder_in_explorer)
        choose_folder_action.triggered.connect(self.choose_folder)

    def _sync_more_menu(self) -> None:
        self.pin_action.blockSignals(True)
        self.pin_action.setChecked(self.always_on_top)
        self.pin_action.blockSignals(False)

        self.lock_action.blockSignals(True)
        self.lock_action.setChecked(self.locked)
        self.lock_action.blockSignals(False)

        self.open_folder_action.setEnabled(bool(self.current_folder))
        for mode, action in self.theme_actions.items():
            action.setChecked(mode == self.theme_mode)
        for color, action in self.accent_actions.items():
            action.setChecked(color == self.accent_color)
        for size, action in self.icon_size_actions.items():
            action.setChecked(size == self.icon_size)
        self._update_view_button_text()

    def _save_window_state(self) -> None:
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def _apply_theme_mode(self, mode: str, initial: bool = False) -> None:
        self.theme_mode = normalize_theme_mode(mode)
        if hasattr(self, "shell"):
            self._refresh_style_sheet()
        if not initial:
            self._save_window_state()

    def _apply_accent_color(self, color: str, initial: bool = False) -> None:
        self.accent_color = normalize_accent_color(color)
        if hasattr(self, "shell"):
            self._refresh_style_sheet()
        if not initial:
            self._save_window_state()

    def choose_accent_color(self) -> None:
        color = QColorDialog.getColor(
            QColor(self.accent_color),
            self,
            "选择强调色",
        )
        if color.isValid():
            self._apply_accent_color(color.name())

    def _apply_icon_size(self, value: int, initial: bool = False) -> None:
        self.icon_size = min((32, 40, 48, 56), key=lambda size: abs(size - int(value)))
        if hasattr(self, "list_view"):
            self.list_view.setIconSize(QSize(self.icon_size, self.icon_size))
            self.list_view.setGridSize(self._icon_grid_size())
        if not initial:
            self._save_window_state()

    def choose_background_opacity(self) -> None:
        value, ok = QInputDialog.getInt(
            self,
            "背景透明度",
            "透明度（20–100%）：",
            value=round(self.background_opacity * 100),
            min=20,
            max=100,
            step=5,
        )
        if ok:
            self._apply_background_opacity(value)

    def rename_box(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            TEXT["rename_box"],
            TEXT["box_name"],
            text=self.box_title,
        )
        if not ok:
            return
        self.box_title = name.strip()
        self._sync_window_title()
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def _sync_window_title(self) -> None:
        display_name = self.box_title or "FolderBox"
        self.title_label.setText(display_name)
        if self.current_folder:
            folder_name = Path(self.current_folder).name or self.current_folder
            self.setWindowTitle(f"{display_name} - {folder_name}")
        else:
            self.setWindowTitle(display_name)

    def _title_label_double_click(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.rename_box()
            event.accept()

    def set_current_folder(
        self,
        folder: str | Path,
        message: str = "",
        record_history: bool = True,
    ) -> None:
        path = Path(folder)
        if not path.exists() or not path.is_dir():
            self.current_folder = ""
            self.show_empty_state(TEXT["select_hint"])
            return

        target = str(path)
        if record_history:
            if self._history_index < 0 or self._history[self._history_index] != target:
                self._history = self._history[: self._history_index + 1]
                self._history.append(target)
                self._history_index = len(self._history) - 1

        if target != self.current_folder and self.search_edit.text():
            self.search_edit.clear()

        self.current_folder = target
        root_index = self.file_model.set_root_path(path)
        self.list_view.setRootIndex(root_index)
        self.details_view.setRootIndex(root_index)
        self._show_current_file_view()
        self.update_path_label()
        self.update_navigation_buttons()
        self.update_folder_state(message or TEXT["loaded"])
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def show_empty_state(self, message: str) -> None:
        self.current_folder = ""
        self.breadcrumb.set_path("")
        self.empty_label.setText(message)
        self.stack.setCurrentWidget(self.empty_label)
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        self.up_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.status_label.setText(message)
        self._sync_window_title()

    def update_path_label(self) -> None:
        self.breadcrumb.set_path(self.current_folder)
        self._sync_window_title()

    def update_navigation_buttons(self) -> None:
        if not self.current_folder:
            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            self.up_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            return

        current = Path(self.current_folder)
        self.back_button.setEnabled(self._history_index > 0)
        self.forward_button.setEnabled(
            0 <= self._history_index < len(self._history) - 1
        )
        self.up_button.setEnabled(current.parent != current and current.parent.exists())
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
        self.update_navigation_buttons()

    def apply_search_filter(self, text: str) -> None:
        self.file_model.set_name_filter(text)
        if self.current_folder:
            message = f"筛选：{text}" if text.strip() else TEXT["ready"]
            self.update_folder_state(message)

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
        style = self.style()
        if self.view_mode == "details":
            self.view_button.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
            )
            self.view_button.setToolTip(TEXT["switch_to_icons"])
            menu_text = TEXT["switch_to_icons"]
        else:
            self.view_button.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            )
            self.view_button.setToolTip(TEXT["switch_to_details"])
            menu_text = TEXT["switch_to_details"]

        if hasattr(self, "view_action"):
            self.view_action.setText(menu_text)

    def toggle_view_mode(self) -> None:
        self.set_view_mode("details" if self.view_mode == "icons" else "icons")

    def set_view_mode(self, mode: str) -> None:
        if mode not in {"icons", "details"}:
            return
        self.view_mode = mode
        self._update_view_button_text()
        if self.current_folder:
            self.update_folder_state()
        if self.manager and hasattr(self.manager, "save_window_states"):
            self.manager.save_window_states()

    def handle_file_view_key(
        self,
        event: QKeyEvent,
        view: QAbstractItemView,
    ) -> bool:
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selected()
            return True
        if event.matches(QKeySequence.StandardKey.Cut):
            self.cut_selected()
            return True
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_to_current_folder()
            return True
        if event.matches(QKeySequence.StandardKey.SelectAll):
            view.selectAll()
            return True
        if event.matches(QKeySequence.StandardKey.Find):
            self.search_edit.setFocus()
            self.search_edit.selectAll()
            return True
        if (
            event.key() == Qt.Key.Key_N
            and event.modifiers()
            == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        ):
            self.create_new_folder()
            return True
        if (
            event.key() == Qt.Key.Key_Left
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.go_back()
            return True
        if (
            event.key() == Qt.Key.Key_Right
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.go_forward()
            return True
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.open_selected()
            return True
        if event.key() == Qt.Key.Key_F2:
            self.rename_selected()
            return True
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
            return True
        if event.key() == Qt.Key.Key_Backspace:
            self.go_to_parent()
            return True
        if event.key() == Qt.Key.Key_F5:
            self.refresh_current_folder()
            return True
        return False

    def clipboard_paths(self, existing_only: bool = True) -> list[str]:
        mime_data = QApplication.clipboard().mimeData()
        if not mime_data or not mime_data.hasUrls():
            return []
        paths: list[str] = []
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            local_path = url.toLocalFile()
            if not existing_only or path_exists(local_path):
                paths.append(local_path)
        return paths

    def has_paste_data(self) -> bool:
        return bool(self.clipboard_paths())

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
            self.manager.open_new_window(self)
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

    def go_back(self) -> None:
        target_index = self._history_index - 1
        while target_index >= 0:
            target = self._history[target_index]
            if path_exists(target) and Path(target).is_dir():
                self._history_index = target_index
                self.set_current_folder(target, "已后退", record_history=False)
                return
            self._history.pop(target_index)
            self._history_index -= 1
            target_index -= 1
        self.update_navigation_buttons()

    def go_forward(self) -> None:
        target_index = self._history_index + 1
        while target_index < len(self._history):
            target = self._history[target_index]
            if path_exists(target) and Path(target).is_dir():
                self._history_index = target_index
                self.set_current_folder(target, "已前进", record_history=False)
                return
            self._history.pop(target_index)
        self.update_navigation_buttons()

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
            self.show_empty_state(TEXT["missing"])
            return
        root_index = self.file_model.refresh_folder()
        self.list_view.setRootIndex(root_index)
        self.details_view.setRootIndex(root_index)
        self.update_path_label()
        self.update_folder_state("\u5df2\u5237\u65b0")

    def _set_clipboard_paths(self, paths: list[str], action: str) -> None:
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
        mime_data.setData(FOLDERBOX_CLIPBOARD_ACTION, action.encode("ascii"))
        QApplication.clipboard().setMimeData(mime_data)

    def _clipboard_action(self) -> str:
        mime_data = QApplication.clipboard().mimeData()
        if not mime_data or not mime_data.hasFormat(FOLDERBOX_CLIPBOARD_ACTION):
            return "copy"
        action = bytes(mime_data.data(FOLDERBOX_CLIPBOARD_ACTION)).decode(
            "ascii",
            errors="ignore",
        )
        return action if action in {"copy", "move"} else "copy"

    def _owns_clipboard(self, paths: list[str]) -> bool:
        return self.clipboard_paths(existing_only=False) == paths and self._clipboard_action() in {
            "copy",
            "move",
        }

    def copy_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        self._set_clipboard_paths(paths, "copy")
        self.update_folder_state(f"已复制 {len(paths)} 个项目")

    def cut_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        self._set_clipboard_paths(paths, "move")
        self.update_folder_state(f"已剪切 {len(paths)} 个项目")

    def paste_to_current_folder(self) -> None:
        if not self.current_folder:
            return
        paths = self.clipboard_paths()
        if not paths:
            return
        move = self._clipboard_action() == "move"
        self._transfer_paths_to_folder(
            paths,
            self.current_folder,
            "移动" if move else "粘贴",
            move=move,
        )

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
        self._transfer_paths_to_folder(paths, destination, "拖入复制", move=False)

    def _start_file_task(
        self,
        task: FunctionTask,
        action_name: str,
        on_finished: Callable[[object], None],
    ) -> None:
        if self._file_task is not None:
            self.status_label.setText("已有文件操作正在进行")
            return

        self._file_task = task
        self._file_task_action = action_name
        self._file_task_on_finished = on_finished
        task.signals.finished.connect(self._on_file_task_finished)
        task.signals.failed.connect(self._on_file_task_failed)
        self.status_label.setText(f"{action_name}中…")
        self.thread_pool.start(task)

    @Slot(object)
    def _on_file_task_finished(self, result: object) -> None:
        callback = self._file_task_on_finished
        self._file_task = None
        self._file_task_action = ""
        self._file_task_on_finished = None
        if callback is not None:
            callback(result)

    @Slot(str)
    def _on_file_task_failed(self, message: str) -> None:
        action_name = self._file_task_action or "文件操作"
        self._file_task = None
        self._file_task_action = ""
        self._file_task_on_finished = None
        self.show_error(f"{action_name}失败", message)
        self.update_folder_state(f"{action_name}失败")

    def _transfer_paths_to_folder(
        self,
        paths: list[str],
        destination: str,
        action_name: str,
        move: bool,
    ) -> None:
        operation = move_items if move else copy_items
        task = FunctionTask(operation, list(paths), destination)
        self._start_file_task(
            task,
            action_name,
            lambda result: self._finish_transfer(
                result,
                action_name,
                move,
                list(paths),
            ),
        )

    def _finish_transfer(
        self,
        result: object,
        action_name: str,
        move: bool,
        original_paths: list[str],
    ) -> None:
        completed, failures = result
        self.refresh_current_folder()

        if move and self._owns_clipboard(original_paths):
            failed_paths = [str(path) for path, _ in failures]
            if failed_paths:
                self._set_clipboard_paths(failed_paths, "move")
            else:
                QApplication.clipboard().clear()

        if failures:
            details = "\n".join(f"{path.name}: {error}" for path, error in failures[:8])
            if len(failures) > 8:
                details += f"\n其余 {len(failures) - 8} 项失败。"
            self.show_error(f"部分项目{action_name}失败", details)
            self.update_folder_state(
                f"已{action_name} {len(completed)} 个项目，{len(failures)} 个失败"
            )
        else:
            self.update_folder_state(f"{action_name}完成，共 {len(completed)} 个项目")

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

        task = FunctionTask(delete_to_recycle_bin, list(paths))
        self._start_file_task(task, "删除", self._finish_delete)

    def _finish_delete(self, result: object) -> None:
        failures = result
        self.refresh_current_folder()
        if failures:
            details = "\n".join(f"{path.name}: {error}" for path, error in failures[:8])
            self.show_error("部分项目删除失败", details)
            self.update_folder_state(f"删除完成，{len(failures)} 个失败")
        else:
            self.update_folder_state("删除完成")

    def create_new_folder(self) -> None:
        if not self.current_folder:
            return
        name, ok = QInputDialog.getText(
            self,
            TEXT["new_folder"],
            TEXT["folder_name"],
            text="新建文件夹",
        )
        if not ok:
            return
        try:
            create_folder(self.current_folder, name)
            self.refresh_current_folder()
            self.update_folder_state("文件夹已创建")
        except FileOperationError as exc:
            self.show_error("新建文件夹失败", str(exc))

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
        cut_action = menu.addAction(TEXT["cut"])
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
        elif selected_action == cut_action:
            self.cut_selected()
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
            new_folder_action = menu.addAction(TEXT["new_folder"])
            refresh_action = menu.addAction(TEXT["refresh"])
            choose_action = menu.addAction(TEXT["choose"])
            new_window_action = menu.addAction(TEXT["new_window"])
            view_action = menu.addAction(TEXT["switch_to_details"] if self.view_mode == "icons" else TEXT["switch_to_icons"])
            open_folder_action = menu.addAction(TEXT["open_folder"])
        else:
            paste_action = None
            new_folder_action = None
            refresh_action = None
            open_folder_action = None
            view_action = None
            new_window_action = menu.addAction(TEXT["new_window"])
            choose_action = menu.addAction(TEXT["choose"])

        menu.addSeparator()
        rename_box_action = menu.addAction(TEXT["rename_box"])
        toggle_lock_action = menu.addAction(TEXT["unlock"] if self.locked else TEXT["lock"])

        selected_action = menu.exec(global_position)
        if self.current_folder and selected_action == paste_action:
            self.paste_to_current_folder()
        elif self.current_folder and selected_action == new_folder_action:
            self.create_new_folder()
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
        elif selected_action == rename_box_action:
            self.rename_box()
        elif selected_action == toggle_lock_action:
            self._apply_locked(not self.locked)

    def snapshot_state(self) -> dict[str, Any]:
        geometry = self.geometry()
        return {
            "folder": self.current_folder if path_exists(self.current_folder) else "",
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
            "always_on_top": self.always_on_top,
            "background_opacity": round(self.background_opacity, 2),
            "view_mode": self.view_mode,
            "box_title": self.box_title,
            "locked": self.locked,
            "theme_mode": self.theme_mode,
            "accent_color": self.accent_color,
            "icon_size": self.icon_size,
        }

    def _on_directory_loaded(self, loaded_path: str) -> None:
        if self.current_folder and Path(loaded_path) == Path(self.current_folder):
            self.update_folder_state(TEXT["loaded"])

    def _title_mouse_press(self, event: QMouseEvent) -> None:
        if self.locked:
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_mouse_move(self, event: QMouseEvent) -> None:
        if self.locked:
            event.ignore()
            return
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
        try:
            if self.manager and hasattr(self.manager, "unregister_window"):
                self.manager.unregister_window(self)
            else:
                self.config.set("windows", [state])
                self.config.save()
        except Exception as exc:
            QMessageBox.warning(self, "\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25", format_exception(exc))
        event.accept()
