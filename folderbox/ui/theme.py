from __future__ import annotations


def build_stylesheet(background_opacity: float) -> str:
    shell_alpha = int(255 * background_opacity)
    list_alpha = int(145 * background_opacity)
    hover_alpha = int(130 * background_opacity)
    button_alpha = int(180 * background_opacity)
    button_hover_alpha = int(225 * background_opacity)
    border_alpha = max(90, int(190 * background_opacity))

    return f"""
    QMainWindow {{ background: transparent; }}
    QFrame#shell {{
        background: rgba(244, 247, 250, {shell_alpha});
        border: 1px solid rgba(122, 132, 145, {border_alpha});
        border-radius: 10px;
    }}
    QWidget#titleBar, QWidget#navigationBar {{ background: transparent; }}
    QLabel#titleLabel {{
        font-weight: 700;
        font-size: 13px;
        color: #111827;
        padding-left: 2px;
    }}
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
    QListView::item:hover, QTreeView::item:hover {{
        background: rgba(255, 255, 255, {hover_alpha});
    }}
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
    QPushButton:hover, QToolButton:hover {{
        background: rgba(255, 255, 255, {button_hover_alpha});
    }}
    QToolButton:checked {{
        background: rgba(96, 165, 250, 170);
        border-color: rgba(37, 99, 235, 180);
    }}
    QToolButton#windowControl {{
        min-width: 26px;
        min-height: 24px;
        padding: 1px 3px;
        border: 0;
        background: transparent;
    }}
    QToolButton#windowControl:hover {{
        background: rgba(255, 255, 255, {button_hover_alpha});
    }}
    QToolButton#windowControl::menu-indicator {{
        image: none;
        width: 0;
    }}
    QMenu {{
        background: rgba(255, 255, 255, 245);
        border: 1px solid rgba(148, 163, 184, 190);
    }}
    QMenu::item {{ padding: 5px 24px 5px 18px; color: #111827; }}
    QMenu::item:selected {{ background: rgba(219, 234, 254, 240); }}
    """
