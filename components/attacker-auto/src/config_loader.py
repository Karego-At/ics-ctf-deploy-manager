from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator, field_validator


# ── Models ────────────────────────────────────────────────────────────────────

    

class Scenario(BaseModel):
    """Scenario definition."""
    name: str
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def name_not_empty(self) -> "Scenario":
        if not self.name.strip():
            raise ValueError("scenario.name must not be empty")
        return self


class AppConfig(BaseModel):
    """Root config object — mirrors the top-level YAML structure."""
    options: dict[str, Any] = Field(default_factory=dict)
    scenario: Scenario


    @field_validator("options", mode="before")
    @classmethod
    def none_to_empty(cls, v: Any) -> Any:
        return v or {}

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load and validate config from a YAML file."""
        raw = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """Load and validate config from a plain dict."""
        return cls.model_validate(data)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def to_yaml(self, path: str | Path | None = None) -> str:
        """Serialise config back to YAML (optionally write to file)."""
        dumped = yaml.dump(
            self.model_dump(),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        if path is not None:
            Path(path).write_text(dumped, encoding="utf-8")
        return dumped


# ── Convenience loader ────────────────────────────────────────────────────────

def load_config(path: str | Path) -> AppConfig:
    """Top-level helper — the only import most callers need."""
    return AppConfig.from_yaml(path)
