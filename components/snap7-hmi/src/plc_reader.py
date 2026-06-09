# plc_reader.py — PLC connection, polling loop, mapping logic

import time
import threading
import snap7
from snap7.type import Areas


START_BYTE    = 20
BYTE_COUNT    = 10


# ── Shared state (written here, read by web.py) ───────────────────────────────
state: dict = {"output": ""}
state_lock  = threading.Lock()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode(data: bytearray) -> str:
    """bytearray → printable ASCII string, nulls/non-printable stripped."""
    return "".join(chr(b) for b in data if 0x20 <= b <= 0x7E).strip()


def _apply_mapping(raw: str, mapping: dict, connected: bool) -> str:
    if not connected:
        return mapping.get("unreachable", "PLC UNREACHABLE")
    for rule in mapping.get("mappings", []):
        if rule.get("input", "") == raw:
            return rule.get("output", "")
    return mapping.get("default", "No match")

# ── Polling thread ────────────────────────────────────────────────────────────

def _poll_loop(plc_ip: str, rack: int, slot: int, tcp_port: int,
               poll_interval: float, mapping: dict) -> None:
    client: snap7.Client | None = None

    while True:
        try:
            if client is None or not client.get_connected():
                client = snap7.Client()
                client.connect(plc_ip, rack, slot, tcp_port)
        except Exception:
            client = None

        if client and client.get_connected():
            try:
                raw = client.read_area(Areas.PE, 0, START_BYTE, BYTE_COUNT)
                output = _apply_mapping(_decode(raw), mapping, connected=True)
            except Exception:
                client = None
                output = _apply_mapping("", mapping, connected=False)
        else:
            output = _apply_mapping("", mapping, connected=False)

        with state_lock:
            state["output"] = output

        time.sleep(poll_interval)


def start(plc_ip: str, rack: int, slot: int, tcp_port: int,
          poll_interval: float, mapping: dict) -> None:
    """Start the background polling thread (daemon — dies with main process)."""
    t = threading.Thread(
        target=_poll_loop,
        args=(plc_ip, rack, slot, tcp_port, poll_interval, mapping),
        daemon=True,
    )
    t.start()