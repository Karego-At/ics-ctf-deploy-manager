import yaml


def load(output_path: str, connection_path: str) -> tuple[dict, dict]:
    """Load output and connection settings from two separate YAML files."""
    with open(output_path, "r", encoding="utf-8") as f:
        output_cfg = yaml.safe_load(f) or {}
    with open(connection_path, "r", encoding="utf-8") as f:
        connection_cfg = yaml.safe_load(f) or {}
    return output_cfg, connection_cfg