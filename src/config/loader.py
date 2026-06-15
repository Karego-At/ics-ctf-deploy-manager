from pydantic import BaseModel, model_validator, Field, field_validator
from pydantic_core import PydanticCustomError
from pydantic import ValidationInfo

from typing import Literal, Annotated, Union
from ipaddress import IPv4Interface
from functools import lru_cache
import yaml
from string import Template

from src.config.devices import AnyDevice
from src.config.components import AnyComponent#, _DRIVER_REGISTRY
from src.config.options import RunOptions, ConnectionOptions
from typing import Any, Literal, Annotated, Union, Type, ClassVar


# ── Setups ────────────────────────────────────────────────────────────────────

class NetworkConfig(BaseModel):
    name: str | None = None
    driver: str
    options: dict | None = None
    ipam: dict | None = None
    args: dict | None = None
    def to_kwargs(self) -> dict:
        data = self.model_dump(
            exclude_none=True,
            exclude_defaults=True,
            exclude={"args"}
        )
        if self.args:
            data.update(self.args)
        return data


class PeerConfig(BaseModel):
    name: str | None = None
    component: str        
    connection_options: ConnectionOptions = Field(default_factory=ConnectionOptions)
    run_options: RunOptions = Field(default_factory=RunOptions)
    settings: Any = None 
    args: dict | None = None
    # @field_validator("component", mode="after")
    # @classmethod
    # def _check_component(cls, v: str, info: ValidationInfo) -> str:
    #     component_map: dict | None = (info.context or {}).get("component_map")
    #     if component_map is not None and v not in component_map:
    #         raise PydanticCustomError(
    #             "unknown_component",
    #             "Unknown component '{component}'. Available: {available}",
    #             {"component": v, "available": sorted(component_map)},
    #         )
    #     return v
    # @model_validator(mode="after")
    # def _parse_settings(self, info: ValidationInfo) -> "PeerConfig":
    #     component_map: dict[str, AnyComponent] | None = (info.context or {}).get("component_map")
    #     if not component_map:
    #         return self

    #     comp = component_map.get(self.component)
    #     if comp is None or comp.driver is None:
    #         if self.settings is not None:
    #             raise PydanticCustomError(
    #                 "unexpected_settings",
    #                 "Component '{component}' has no driver, but settings were provided",
    #                 {"component": self.component},
    #             )
    #         return self

    #     driver_cls = _DRIVER_REGISTRY.get(comp.driver)
    #     if driver_cls is None:
    #         raise PydanticCustomError(
    #             "unknown_driver",
    #             "Unknown driver '{driver}'. Registered: {available}",
    #             {"driver": comp.driver, "available": sorted(_DRIVER_REGISTRY)},
    #         )

    #     raw = self.settings if isinstance(self.settings, dict) else {}
    #     self.settings = driver_cls.Settings.model_validate(raw)
    #     return self




class SetupConfig(BaseModel):
    # name: str | None = None
    network: NetworkConfig | None = None
    devices: list[str] = Field(default_factory=list)  
    peers: list[PeerConfig] = Field(default_factory=list)


# ── Root ──────────────────────────────────────────────────────────────────────


class InfrastructureConfig(BaseModel):
    """Devices and components — loaded once at startup."""
    devices: list[AnyDevice]
    components: list[AnyComponent]

class ChallengeConfig(BaseModel):
    """Setups — can be loaded from file or constructed via API."""
    setups: list[SetupConfig] = Field(default_factory=list)

@lru_cache
def get_infrastructure(path: str, components_path: str) -> InfrastructureConfig:
    print("Reading infrastructure config...")
    with open(path) as f:
        raw = f.read()
    resolved = Template(raw).substitute(components_path=components_path)
    data = yaml.safe_load(resolved)
    return InfrastructureConfig(**data)


# def get_setups(path: str, infra: InfrastructureConfig) -> ChallengeConfig:
#     with open(path) as f:
#         data = yaml.safe_load(f)

#     return ChallengeConfig.model_validate(
#         data,
#         context={"component_map": {c.name: c for c in infra.components}},
#     )



def get_challenge(path: str) -> ChallengeConfig:
    """Load setups from a separate file (or skip — API will provide them)."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return ChallengeConfig(**data)