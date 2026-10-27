"""Minimal Source RCON client for the Minecraft server console."""
import socket
import struct
import threading

LOGIN, COMMAND, RESPONSE = 3, 2, 0


class RconError(Exception):
    pass


class Rcon:
    """One connection, reopened when it drops; command() is safe to call from several threads."""

    def __init__(self, host, port, password, timeout=30):
        self.host, self.port, self.password, self.timeout = host, port, password, timeout
        self._sock = None
        self._lock = threading.Lock()
        self._next_id = 1

    def _send(self, kind, body):
        request_id = self._next_id
        self._next_id = self._next_id % 2_000_000_000 + 1
        payload = struct.pack("<ii", request_id, kind) + body.encode("utf-8") + b"\x00\x00"
        self._sock.sendall(struct.pack("<i", len(payload)) + payload)
        return request_id

    def _recv_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self._sock.recv(size - len(data))
            if not chunk:
                raise RconError("connection closed")
            data += chunk
        return data

    def _recv(self):
        (size,) = struct.unpack("<i", self._recv_exact(4))
        packet = self._recv_exact(size)
        request_id, kind = struct.unpack("<ii", packet[:8])
        return request_id, kind, packet[8:-2].decode("utf-8", errors="replace")

    def _connect(self):
        self.close()
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        request_id = self._send(LOGIN, self.password)
        while True:
            answer_id, kind, _ = self._recv()
            if kind == 2:   # auth response
                break
        if answer_id == -1 or answer_id != request_id:
            self.close()
            raise RconError("RCON login failed")

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def command(self, text):
        """Run a console command and return its output."""
        with self._lock:
            for attempt in (1, 2):
                try:
                    if self._sock is None:
                        self._connect()
                    request_id = self._send(COMMAND, text)
                    while True:
                        answer_id, _, body = self._recv()
                        if answer_id == request_id:
                            return body
                except (OSError, RconError):
                    self.close()
                    if attempt == 2:
                        raise
