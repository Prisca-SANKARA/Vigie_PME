import socket
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scanner.port_scan import _is_port_open


def test_closed_port_on_localhost_returns_false():
    # Port peu susceptible d'être utilisé localement pendant les tests.
    assert _is_port_open("127.0.0.1", 59999, timeout=0.5) is False


def test_open_port_on_localhost_returns_true():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    thread = threading.Thread(target=server.accept, daemon=True)
    thread.start()

    try:
        assert _is_port_open("127.0.0.1", port, timeout=1.0) is True
    finally:
        server.close()
