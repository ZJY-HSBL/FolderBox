from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "FolderBoxSingleInstanceV1"


class InstanceBridge(QObject):
    requestReceived = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._accept_connections)
        self._buffers: dict[QLocalSocket, bytearray] = {}

    def listen(self) -> bool:
        if self.server.listen(SERVER_NAME):
            return True
        QLocalServer.removeServer(SERVER_NAME)
        return self.server.listen(SERVER_NAME)

    def _accept_connections(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self._buffers[socket] = bytearray()
            socket.readyRead.connect(lambda sock=socket: self._read_socket(sock))
            socket.disconnected.connect(lambda sock=socket: self._drop_socket(sock))

    def _read_socket(self, socket: QLocalSocket) -> None:
        buffer = self._buffers.get(socket)
        if buffer is None:
            return
        buffer.extend(bytes(socket.readAll()))

        while b"\n" in buffer:
            raw, _, rest = buffer.partition(b"\n")
            self._buffers[socket] = bytearray(rest)
            buffer = self._buffers[socket]
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            folder = str(payload.get("folder", "") or "")
            self.requestReceived.emit(folder)

    def _drop_socket(self, socket: QLocalSocket) -> None:
        self._buffers.pop(socket, None)
        socket.deleteLater()


def notify_existing_instance(folder: str = "", timeout_ms: int = 300) -> bool:
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(timeout_ms):
        socket.abort()
        return False

    payload = json.dumps({"folder": folder}, ensure_ascii=False).encode("utf-8") + b"\n"
    if socket.write(payload) < 0:
        socket.abort()
        return False
    socket.flush()
    delivered = socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return delivered
