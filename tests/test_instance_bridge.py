import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication

from folderbox.instance_bridge import (
    SERVER_NAME,
    InstanceBridge,
    notify_existing_instance,
)


def test_instance_bridge_round_trip() -> None:
    app = QApplication.instance() or QApplication([])
    QLocalServer.removeServer(SERVER_NAME)

    bridge = InstanceBridge(app)
    received: list[str] = []
    bridge.requestReceived.connect(received.append)

    assert bridge.listen()
    assert notify_existing_instance("D:/Research")

    for _ in range(20):
        app.processEvents()
        if received:
            break

    assert received == ["D:/Research"]

    bridge.server.close()
    QLocalServer.removeServer(SERVER_NAME)
