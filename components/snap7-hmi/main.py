# main.py — entry point
#
# dependencies:  pip install python-snap7 flask pyyaml
# launch:       python main.py
# browser:      http://<host-ip>:5000

import src.plc_reader as plc_reader
from src.config import load
from src.web import app
from src import web
import os




_CONFIG_FILE = "config.yaml"


if __name__ == "__main__":
    _mapping, _conn = load(_CONFIG_FILE)

    PLC_IP        = _conn.get("ip",            "192.168.1.55")
    TCP_PORT      = _conn.get("tcp_port",      102)
    RACK          = _conn.get("rack",          0)
    SLOT          = _conn.get("slot",          1)
    POLL_INTERVAL = _conn.get("poll_interval", 1.0)

    web.poll_interval = POLL_INTERVAL
    web.template_path = os.path.join(os.getcwd(), "templates")

    plc_reader.start(
        plc_ip=PLC_IP,
        rack=RACK,
        slot=SLOT,
        tcp_port=TCP_PORT,
        poll_interval=POLL_INTERVAL,
        mapping=_mapping,
    )

    print(f"[HMI] PLC      : {PLC_IP}:{TCP_PORT}  rack={RACK}  slot={SLOT}")
    # print(f"[HMI] Range    : IB{START_BYTE}–IB{START_BYTE + BYTE_COUNT - 1}")
    print(f"[HMI] Poll     : {POLL_INTERVAL}s")
    print(f"[HMI] Web      : http://0.0.0.0:5000")
    print(f"[HMI] Ctrl+C to stop")

    os.environ["PYTHONUNBUFFERED"] = "1"

    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)