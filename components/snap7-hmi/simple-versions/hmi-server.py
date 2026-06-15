"""
dependencies:
    pip install python-snap7 flask pyyaml

launch:
    python hmi_server.py

browser:
    http://<host-ip>:5000
"""

import time
import threading
import yaml
import snap7
from snap7.type import Areas
from flask import Flask, Response, render_template_string, stream_with_context
import json
import os

# ─────────────────────────────────────────────
#  Connection & read configuration
# ─────────────────────────────────────────────
PLC_IP      = "192.168.1.55"
RACK        = 0
SLOT        = 1
TCP_PORT    = 102

START_BYTE  = 20
BYTE_COUNT  = 10

POLL_INTERVAL = 1.0          # seconds between PLC polls
MAPPING_FILE  = os.path.join(os.path.dirname(__file__), "mapping.yaml")

# ─────────────────────────────────────────────
#  Global state (written by poller, read by SSE)
#  Intentionally minimal — browser sees only the
#  mapped output string, nothing about the PLC.
# ─────────────────────────────────────────────
state = {
    "output": "",
}
state_lock = threading.Lock()

# ─────────────────────────────────────────────
#  YAML mapping loader
# ─────────────────────────────────────────────

def load_mapping(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def apply_mapping(raw_string: str, mapping: dict, connected: bool) -> str:
    if not connected:
        return mapping.get("unreachable", "PLC UNREACHABLE")

    for rule in mapping.get("mappings", []):
        if rule.get("input", "") == raw_string:
            return rule.get("output", "")

    return mapping.get("default", "No match")

# ─────────────────────────────────────────────
#  PLC polling thread
# ─────────────────────────────────────────────

def decode_string(data: bytearray) -> str:
    chars = ""
    for b in data:
        chars += chr(b) if 0x20 <= b <= 0x7E else ""
    return chars.rstrip("\x00").strip()


def plc_poller():
    client: snap7.Client | None = None

    while True:
        mapping = load_mapping(MAPPING_FILE)

        # Try to connect / reconnect
        try:
            if client is None or not client.get_connected():
                client = snap7.Client()
                client.connect(PLC_IP, RACK, SLOT, TCP_PORT)
        except Exception:
            client = None

        if client and client.get_connected():
            try:
                raw: bytearray = client.read_area(
                    area      = Areas.PE,
                    db_number = 0,
                    start     = START_BYTE,
                    size      = BYTE_COUNT,
                )
                raw_string = decode_string(raw)
                output     = apply_mapping(raw_string, mapping, connected=True)
            except Exception:
                client = None
                output = apply_mapping("", mapping, connected=False)
        else:
            output = apply_mapping("", mapping, connected=False)

        with state_lock:
            state["output"] = output

        time.sleep(POLL_INTERVAL)

# ─────────────────────────────────────────────
#  Flask app
# ─────────────────────────────────────────────
app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HMI</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    height: 100%;
    background: #0a0c0f;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Share Tech Mono', 'Courier New', monospace;
  }
  #msg {
    font-size: clamp(24px, 4vw, 48px);
    color: #e8a020;
    letter-spacing: 0.05em;
    text-align: center;
    padding: 0 32px;
    word-break: break-word;
    max-width: 900px;
  }
</style>
</head>
<body>
  <div id="msg">—</div>
<script>
  const es = new EventSource("/stream");
  es.onmessage = function(e) {
    const d = JSON.parse(e.data);
    document.getElementById("msg").textContent = d.output || "—";
  };
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/stream")
def stream():
    """Server-Sent Events endpoint — pushes state updates to the browser."""
    @stream_with_context
    def event_stream():
        while True:
            with state_lock:
                payload = json.dumps(dict(state))
            yield f"data: {payload}\n\n"
            time.sleep(POLL_INTERVAL)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # important for nginx proxying
        },
    )


@app.route("/api/state")
def api_state():
    """JSON snapshot — useful for custom dashboards or monitoring."""
    with state_lock:
        return json.dumps(dict(state)), 200, {"Content-Type": "application/json"}


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Start PLC poller in background thread
    t = threading.Thread(target=plc_poller, daemon=True)
    t.start()

    print(f"[HMI] PLC target : {PLC_IP}:{TCP_PORT}  rack={RACK}  slot={SLOT}")
    print(f"[HMI] Read range : IB{START_BYTE} – IB{START_BYTE + BYTE_COUNT - 1}")
    print(f"[HMI] Mapping    : {MAPPING_FILE}")
    print(f"[HMI] Web server : http://0.0.0.0:5000")
    print(f"[HMI] Press Ctrl+C to stop")

    # host="0.0.0.0" makes it accessible on the local network
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)