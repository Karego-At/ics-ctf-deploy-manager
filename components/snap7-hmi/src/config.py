import os
import yaml

# ── Config file path ──────────────────────────

def load(path: str) -> tuple[dict, dict]:
    """Load output_settings and connection_settings from config.yaml"""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    output_cfg = raw.get("output_settings", {})
    connection_cfg = raw.get("connection_settings", {})
    return output_cfg, connection_cfg