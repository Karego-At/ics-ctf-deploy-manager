# main.py — entry point
#
# dependencies:  pip install python-snap7 flask pyyaml
# launch:       python main.py
# browser:      http://<host-ip>:5000

import plc_reader
from config import PLC_IP, TCP_PORT, RACK, SLOT, START_BYTE, BYTE_COUNT, POLL_INTERVAL
from web import app

if __name__ == "__main__":
    plc_reader.start()

    print(f"[HMI] PLC      : {PLC_IP}:{TCP_PORT}  rack={RACK}  slot={SLOT}")
    print(f"[HMI] Range    : IB{START_BYTE}–IB{START_BYTE + BYTE_COUNT - 1}")
    print(f"[HMI] Poll     : {POLL_INTERVAL}s")
    print(f"[HMI] Web      : http://0.0.0.0:5000")
    print(f"[HMI] Ctrl+C to stop")

    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
    