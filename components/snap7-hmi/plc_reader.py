# plc_reader.py — PLC connection, polling loop, mapping logic

import time
import threading
import snap7
from snap7.type import Areas

from config import (
    PLC_IP, RACK, SLOT, TCP_PORT,
    START_BYTE, BYTE_COUNT,
    POLL_INTERVAL, MAPPING,
)

# ── Shared state (written here, read by web.py) ───────────────────────────────
state: dict      = {"output": ""}
state_lock       = threading.Lock()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode(data: bytearray) -> str:
    """bytearray → printable ASCII string, nulls/non-printable stripped."""
    return "".join(chr(b) for b in data if 0x20 <= b <= 0x7E).strip()


def _apply_mapping(raw: str, connected: bool) -> str:
    if not connected:
        return MAPPING.get("unreachable", "PLC UNREACHABLE")
    for rule in MAPPING.get("mappings", []):
        if rule.get("input", "") == raw:
            return rule.get("output", "")
    return MAPPING.get("default", "No match")

# ── Polling thread ────────────────────────────────────────────────────────────

def _poll_loop() -> None:
    client: snap7.Client | None = None

    while True:
        # reconnect if needed
        try:
            if client is None or not client.get_connected():
                client = snap7.Client()
                client.connect(PLC_IP, RACK, SLOT, TCP_PORT)
        except Exception:
            client = None

        if client and client.get_connected():
            try:
                raw = client.read_area(Areas.PE, 0, START_BYTE, BYTE_COUNT)
                output = _apply_mapping(_decode(raw), connected=True)
            except Exception:
                client = None
                output = _apply_mapping("", connected=False)
        else:
            output = _apply_mapping("", connected=False)

        with state_lock:
            state["output"] = output

        time.sleep(POLL_INTERVAL)


def start() -> None:
    """Start the background polling thread (daemon — dies with main process)."""
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()