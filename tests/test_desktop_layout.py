from PySide6.QtCore import QPoint, QRect, QSize

from folderbox.desktop_layout import layout_rectangles, placement_position, snapped_position


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



def test_grid_layout_balances_four_boxes() -> None:
    screen = QRect(0, 0, 1200, 800)

    rectangles = layout_rectangles("grid", 4, screen, gap=8)

    assert len(rectangles) == 4
    assert rectangles[0].topLeft() == QPoint(8, 8)
    assert rectangles[0].width() >= 320
    assert rectangles[0].height() >= 340
    assert not rectangles[0].intersects(rectangles[1])
    assert not rectangles[0].intersects(rectangles[2])


def test_columns_layout_wraps_when_boxes_would_be_too_narrow() -> None:
    screen = QRect(0, 0, 1000, 800)

    rectangles = layout_rectangles("columns", 6, screen, gap=8)

    assert len(rectangles) == 6
    assert len({rect.y() for rect in rectangles}) > 1


def test_rows_layout_wraps_when_boxes_would_be_too_short() -> None:
    screen = QRect(0, 0, 1400, 700)

    rectangles = layout_rectangles("rows", 5, screen, gap=8)

    assert len(rectangles) == 5
    assert len({rect.x() for rect in rectangles}) > 1


def test_cascade_layout_offsets_boxes() -> None:
    screen = QRect(0, 0, 1200, 800)

    rectangles = layout_rectangles("cascade", 3, screen, gap=8)

    assert rectangles[1].x() > rectangles[0].x()
    assert rectangles[1].y() > rectangles[0].y()
    assert rectangles[2].size() == rectangles[0].size()


def test_unknown_layout_mode_is_rejected() -> None:
    try:
        layout_rectangles("unknown", 2, QRect(0, 0, 1000, 800))
    except ValueError as exc:
        assert "Unknown layout mode" in str(exc)
    else:
        raise AssertionError("Expected unknown layout mode to fail")
