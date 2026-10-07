from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QRect, QSize


def _nearest(value: int, candidates: list[int], threshold: int) -> int:
    if not candidates:
        return value
    candidate = min(candidates, key=lambda item: abs(item - value))
    return candidate if abs(candidate - value) <= threshold else value


def snapped_position(
    desired: QPoint,
    size: QSize,
    screen: QRect,
    peers: list[QRect],
    threshold: int = 12,
    gap: int = 8,
) -> QPoint:
    width = size.width()
    height = size.height()

    x_candidates = [
        screen.left(),
        screen.left() + screen.width() - width,
    ]
    y_candidates = [
        screen.top(),
        screen.top() + screen.height() - height,
    ]

    for peer in peers:
        x_candidates.extend(
            [
                peer.left(),
                peer.left() + peer.width() - width,
                peer.right() + 1 + gap,
                peer.left() - width - gap,
            ]
        )
        y_candidates.extend(
            [
                peer.top(),
                peer.top() + peer.height() - height,
                peer.bottom() + 1 + gap,
                peer.top() - height - gap,
            ]
        )

    return QPoint(
        _nearest(desired.x(), x_candidates, threshold),
        _nearest(desired.y(), y_candidates, threshold),
    )


def placement_position(
    placement: str,
    current: QRect,
    screen: QRect,
    margin: int = 0,
) -> QPoint:
    left = screen.left() + margin
    right = screen.left() + screen.width() - current.width() - margin
    top = screen.top() + margin
    bottom = screen.top() + screen.height() - current.height() - margin

    if placement == "left":
        return QPoint(left, max(top, min(current.y(), bottom)))
    if placement == "right":
        return QPoint(right, max(top, min(current.y(), bottom)))
    if placement == "top":
        return QPoint(max(left, min(current.x(), right)), top)
    if placement == "bottom":
        return QPoint(max(left, min(current.x(), right)), bottom)
    if placement == "center":
        return QPoint(
            screen.left() + (screen.width() - current.width()) // 2,
            screen.top() + (screen.height() - current.height()) // 2,
        )
    raise ValueError(f"Unknown placement: {placement}")



def layout_rectangles(
    mode: str,
    count: int,
    screen: QRect,
    gap: int = 8,
    cascade_size: QSize | None = None,
) -> list[QRect]:
    if count <= 0:
        return []

    if cascade_size is None:
        cascade_size = QSize(420, 520)

    max_columns = max(1, (screen.width() - gap) // (320 + gap))
    max_rows = max(1, (screen.height() - gap) // (340 + gap))

    if mode == "grid":
        columns = min(max_columns, max(1, math.ceil(math.sqrt(count))))
        rows = max(1, math.ceil(count / columns))
    elif mode == "columns":
        columns = min(count, max_columns)
        rows = max(1, math.ceil(count / columns))
    elif mode == "rows":
        rows = min(count, max_rows)
        columns = max(1, math.ceil(count / rows))
    elif mode == "cascade":
        width = min(cascade_size.width(), max(320, screen.width() - gap * 2))
        height = min(cascade_size.height(), max(340, screen.height() - gap * 2))
        max_x = max(screen.left() + gap, screen.right() - width + 1 - gap)
        max_y = max(screen.top() + gap, screen.bottom() - height + 1 - gap)
        step = 28
        rectangles: list[QRect] = []
        for index in range(count):
            x = min(screen.left() + gap + index * step, max_x)
            y = min(screen.top() + gap + index * step, max_y)
            rectangles.append(QRect(x, y, width, height))
        return rectangles
    else:
        raise ValueError(f"Unknown layout mode: {mode}")

    usable_width = max(1, screen.width() - gap * (columns + 1))
    usable_height = max(1, screen.height() - gap * (rows + 1))
    cell_width = max(1, usable_width // columns)
    cell_height = max(1, usable_height // rows)

    rectangles = []
    for index in range(count):
        row = index // columns
        column = index % columns
        x = screen.left() + gap + column * (cell_width + gap)
        y = screen.top() + gap + row * (cell_height + gap)
        width = cell_width
        height = cell_height

        if column == columns - 1:
            width = screen.right() - gap - x + 1
        if row == rows - 1:
            height = screen.bottom() - gap - y + 1

        rectangles.append(QRect(x, y, width, height))
    return rectangles
