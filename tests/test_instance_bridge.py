import os
import subprocess
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication

from folderbox.instance_bridge import SERVER_NAME, InstanceBridge


def test_instance_bridge_round_trip() -> None:
    app = QApplication.instance() or QApplication([])
    QLocalServer.removeServer(SERVER_NAME)

    bridge = InstanceBridge(app)
    received: list[str] = []
    bridge.requestReceived.connect(received.append)

    assert bridge.listen()

    child_code = (
        "from PySide6.QtCore import QCoreApplication;"
        "from folderbox.instance_bridge import notify_existing_instance;"
        "app=QCoreApplication([]);"
        "raise SystemExit(0 if notify_existing_instance('D:/Research', 2000) else 1)"
    )
    child = subprocess.Popen([sys.executable, "-c", child_code])

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (child.poll() is None or not received):
        app.processEvents()
        time.sleep(0.005)

    exit_code = child.wait(timeout=1)
    app.processEvents()

    assert exit_code == 0
    assert received == ["D:/Research"]

    bridge.server.close()
    QLocalServer.removeServer(SERVER_NAME)
