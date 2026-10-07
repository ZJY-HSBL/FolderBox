from PySide6.QtCore import QPoint, QRect, QSize

from folderbox.desktop_layout import placement_position, snapped_position


def test_snaps_to_screen_left_edge() -> None:
    result = snapped_position(
        QPoint(7, 100),
        QSize(320, 400),
        QRect(0, 0, 1920, 1080),
        [],
    )

    assert result == QPoint(0, 100)


def test_snaps_next_to_peer_box() -> None:
    peer = QRect(100, 100, 300, 400)
    result = snapped_position(
        QPoint(409, 100),
        QSize(320, 400),
        QRect(0, 0, 1920, 1080),
        [peer],
    )

    assert result == QPoint(408, 100)


def test_does_not_snap_outside_threshold() -> None:
    result = snapped_position(
        QPoint(40, 60),
        QSize(320, 400),
        QRect(0, 0, 1920, 1080),
        [],
        threshold=12,
    )

    assert result == QPoint(40, 60)


def test_placement_positions_use_available_screen() -> None:
    screen = QRect(10, 20, 1000, 800)
    current = QRect(300, 250, 320, 400)

    assert placement_position("left", current, screen, margin=8).x() == 18
    assert placement_position("right", current, screen, margin=8).x() == 682
    assert placement_position("top", current, screen, margin=8).y() == 28
    assert placement_position("bottom", current, screen, margin=8).y() == 412
    assert placement_position("center", current, screen) == QPoint(350, 220)
