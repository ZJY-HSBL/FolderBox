from __future__ import annotations

from PySide6.QtCore import QPoint, QRect


def detect_edge(geometry: QRect, screen: QRect, tolerance: int = 12) -> str | None:
    distances = {
        "left": abs(geometry.left() - screen.left()),
        "right": abs(geometry.right() - screen.right()),
        "top": abs(geometry.top() - screen.top()),
        "bottom": abs(geometry.bottom() - screen.bottom()),
    }
    edge, distance = min(distances.items(), key=lambda item: item[1])
    return edge if distance <= tolerance else None


def collapsed_position(
    edge: str,
    geometry: QRect,
    screen: QRect,
    strip: int = 10,
) -> QPoint:
    width = geometry.width()
    height = geometry.height()

    min_x = screen.left()
    max_x = screen.right() - width + 1
    min_y = screen.top()
    max_y = screen.bottom() - height + 1

    x = max(min_x, min(geometry.x(), max_x))
    y = max(min_y, min(geometry.y(), max_y))

    if edge == "left":
        return QPoint(screen.left() - width + strip, y)
    if edge == "right":
        return QPoint(screen.right() - strip + 1, y)
    if edge == "top":
        return QPoint(x, screen.top() - height + strip)
    if edge == "bottom":
        return QPoint(x, screen.bottom() - strip + 1)
    raise ValueError(f"Unknown edge: {edge}")
