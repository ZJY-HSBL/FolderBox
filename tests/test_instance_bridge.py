import os
import threading
import time

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
    send_result: list[bool] = []
    bridge.requestReceived.connect(received.append)

    assert bridge.listen()

    sender = threading.Thread(
        target=lambda: send_result.append(
            notify_existing_instance("D:/Research", timeout_ms=1000)
        )
    )
    sender.start()

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and (sender.is_alive() or not received):
        app.processEvents()
        time.sleep(0.005)

    sender.join(timeout=1)
    app.processEvents()

    assert send_result == [True]
    assert received == ["D:/Research"]

    bridge.server.close()
    QLocalServer.removeServer(SERVER_NAME)
