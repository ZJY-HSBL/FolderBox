from __future__ import annotations

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
