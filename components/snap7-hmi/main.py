import src.plc_reader as plc_reader
from src.config import load
from src.web import app
from src import web
import os


_OUTPUT_CONFIG     = "output_config.yaml"
_CONNECTION_CONFIG = "connection_config.yaml"
# CONF_FOLDER = os.path.join(os.getcwd(), "config")
CONF_FOLDER = "/app/config"


if __name__ == "__main__":

    out_conf = os.path.join(CONF_FOLDER, _OUTPUT_CONFIG)
    con_conf = os.path.join(CONF_FOLDER, _CONNECTION_CONFIG)

    _mapping, _conn = load(out_conf, con_conf)

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
    print(f"[HMI] Poll     : {POLL_INTERVAL}s")
    print(f"[HMI] Web      : http://0.0.0.0:5000")
    print(f"[HMI] Ctrl+C to stop")

    os.environ["PYTHONUNBUFFERED"] = "1"
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)