from PySide6.QtCore import QPoint, QRect

from folderbox.edge_peek import collapsed_position, detect_edge


def test_detects_nearest_screen_edge() -> None:
    screen = QRect(0, 0, 1920, 1080)

    assert detect_edge(QRect(0, 100, 420, 520), screen) == "left"
    assert detect_edge(QRect(1500, 100, 420, 520), screen) == "right"
    assert detect_edge(QRect(300, 0, 420, 520), screen) == "top"
    assert detect_edge(QRect(300, 560, 420, 520), screen) == "bottom"


def test_does_not_detect_edge_outside_tolerance() -> None:
    screen = QRect(0, 0, 1920, 1080)

    assert detect_edge(QRect(40, 60, 420, 520), screen, tolerance=12) is None


def test_collapsed_positions_leave_trigger_strip_visible() -> None:
    screen = QRect(0, 0, 1920, 1080)
    geometry = QRect(0, 100, 420, 520)

    assert collapsed_position("left", geometry, screen, strip=10) == QPoint(-410, 100)
    assert collapsed_position("right", geometry, screen, strip=10) == QPoint(1910, 100)
    assert collapsed_position("top", geometry, screen, strip=10) == QPoint(0, -510)
    assert collapsed_position("bottom", geometry, screen, strip=10) == QPoint(0, 1070)


def test_unknown_edge_is_rejected() -> None:
    try:
        collapsed_position("unknown", QRect(0, 0, 420, 520), QRect(0, 0, 1920, 1080))
    except ValueError as exc:
        assert "Unknown edge" in str(exc)
    else:
        raise AssertionError("Expected unknown edge to fail")
