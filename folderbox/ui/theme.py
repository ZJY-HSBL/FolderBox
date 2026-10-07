from __future__ import annotations

DEFAULT_ACCENT_COLOR = "#3b82f6"
THEME_MODES = {"light", "dark"}


def normalize_accent_color(value: str) -> str:
    text = str(value or "").strip().lower()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
        except ValueError:
            pass
        else:
            return text
    return DEFAULT_ACCENT_COLOR


def normalize_theme_mode(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in THEME_MODES else "light"


def _rgb(value: str) -> tuple[int, int, int]:
    color = normalize_accent_color(value)
    return tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))


def build_stylesheet(
    background_opacity: float,
    accent_color: str = DEFAULT_ACCENT_COLOR,
    theme_mode: str = "light",
) -> str:
    theme_mode = normalize_theme_mode(theme_mode)
    accent_color = normalize_accent_color(accent_color)
    accent_r, accent_g, accent_b = _rgb(accent_color)

    if theme_mode == "dark":
        shell_rgb = (24, 28, 36)
        list_rgb = (17, 24, 39)
        hover_rgb = (51, 65, 85)
        button_rgb = (30, 41, 59)
        button_hover_rgb = (51, 65, 85)
        border_rgb = (71, 85, 105)
        text_color = "#f8fafc"
        secondary_text = "#e2e8f0"
        menu_rgb = (30, 41, 59)
        menu_selected_rgb = (51, 65, 85)
    else:
        shell_rgb = (244, 247, 250)
        list_rgb = (255, 255, 255)
        hover_rgb = (255, 255, 255)
        button_rgb = (255, 255, 255)
        button_hover_rgb = (255, 255, 255)
        border_rgb = (122, 132, 145)
        text_color = "#111827"
        secondary_text = "#1f2937"
        menu_rgb = (255, 255, 255)
        menu_selected_rgb = (219, 234, 254)

    shell_alpha = int(255 * background_opacity)
    list_alpha = int((185 if theme_mode == "dark" else 145) * background_opacity)
    hover_alpha = int((210 if theme_mode == "dark" else 130) * background_opacity)
    button_alpha = int((205 if theme_mode == "dark" else 180) * background_opacity)
    button_hover_alpha = int((235 if theme_mode == "dark" else 225) * background_opacity)
    border_alpha = max(90, int(190 * background_opacity))

    shell = ", ".join(map(str, shell_rgb))
    list_color = ", ".join(map(str, list_rgb))
    hover = ", ".join(map(str, hover_rgb))
    button = ", ".join(map(str, button_rgb))
    button_hover = ", ".join(map(str, button_hover_rgb))
    border = ", ".join(map(str, border_rgb))
    menu = ", ".join(map(str, menu_rgb))
    menu_selected = ", ".join(map(str, menu_selected_rgb))

    return f"""
    QMainWindow {{ background: transparent; }}
    QFrame#shell {{
        background: rgba({shell}, {shell_alpha});
        border: 1px solid rgba({accent_r}, {accent_g}, {accent_b}, {border_alpha});
        border-radius: 10px;
    }}
    QWidget#titleBar, QWidget#navigationBar {{ background: transparent; }}
    QLabel#titleLabel {{
        font-weight: 700;
        font-size: 13px;
        color: {text_color};
        padding-left: 2px;
    }}
    QLabel#statusLabel, QLabel#emptyLabel, QLabel {{ color: {secondary_text}; }}
    QLabel#emptyLabel {{ font-size: 14px; }}
    QListView, QTreeView {{
        background: rgba({list_color}, {list_alpha});
        border: 1px solid rgba({border}, {border_alpha});
        border-radius: 8px;
        padding: 8px;
        outline: none;
        color: {text_color};
    }}
    QListView::item, QTreeView::item {{
        color: {text_color};
        padding: 6px;
        border-radius: 7px;
    }}
    QListView::item:hover, QTreeView::item:hover {{
        background: rgba({hover}, {hover_alpha});
    }}
    QListView::item:selected, QTreeView::item:selected {{
        background: rgba({accent_r}, {accent_g}, {accent_b}, 145);
        color: {text_color};
    }}
    QHeaderView::section {{
        background: rgba({button}, {button_alpha});
        color: {text_color};
        border: 0;
        border-right: 1px solid rgba({border}, {border_alpha});
        padding: 5px 7px;
    }}
    QPushButton, QToolButton {{
        min-height: 24px;
        padding: 3px 8px;
        border: 1px solid rgba({border}, {border_alpha});
        border-radius: 6px;
        background: rgba({button}, {button_alpha});
        color: {text_color};
    }}
    QPushButton:hover, QToolButton:hover {{
        background: rgba({button_hover}, {button_hover_alpha});
    }}
    QToolButton:checked {{
        background: rgba({accent_r}, {accent_g}, {accent_b}, 155);
        border-color: {accent_color};
    }}
    QToolButton#windowControl {{
        min-width: 26px;
        min-height: 24px;
        padding: 1px 3px;
        border: 0;
        background: transparent;
    }}
    QToolButton#windowControl:hover {{
        background: rgba({button_hover}, {button_hover_alpha});
    }}
    QToolButton#windowControl::menu-indicator {{
        image: none;
        width: 0;
    }}
    QLineEdit {{
        min-height: 24px;
        padding: 3px 8px;
        border: 1px solid rgba({border}, {border_alpha});
        border-radius: 6px;
        background: rgba({button}, {button_alpha});
        color: {text_color};
        selection-background-color: rgba({accent_r}, {accent_g}, {accent_b}, 170);
    }}
    QLineEdit:focus {{
        border-color: {accent_color};
        background: rgba({button_hover}, {button_hover_alpha});
    }}
    QLabel#breadcrumbSeparator {{
        color: {secondary_text};
        padding: 0 1px;
    }}
    QMenu {{
        background: rgba({menu}, 248);
        color: {text_color};
        border: 1px solid rgba({border}, 190);
    }}
    QMenu::item {{ padding: 5px 24px 5px 18px; color: {text_color}; }}
    QMenu::item:selected {{ background: rgba({menu_selected}, 240); }}
    """
