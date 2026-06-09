# config.py — connection constants + mapping loaded once at startup

import os
import yaml

# ── PLC connection ────────────────────────────
PLC_IP        = "192.168.1.55"
RACK          = 0
SLOT          = 1
TCP_PORT      = 102

# ── Read range ────────────────────────────────
START_BYTE    = 20
BYTE_COUNT    = 10

# ── Polling ───────────────────────────────────
POLL_INTERVAL = 1.0   # seconds

# ── Mapping ───────────────────────────────────
_MAPPING_FILE = os.path.join(os.path.dirname(__file__), "mapping.yaml")

def _load() -> dict:
    with open(_MAPPING_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return raw.get("output_settings", {})

# Loaded once — all modules import this object directly
MAPPING: dict = _load()