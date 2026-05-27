from pydantic import BaseModel, model_validator, Field
from typing import Literal, Annotated, Union
from ipaddress import IPv4Interface
from functools import lru_cache
import yaml
from string import Template

from src.config.devices import AnyDevice
from src.config.components import AnyComponent, _DRIVER_REGISTRY, _COMPONENT_REGISTRY
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
    settings: dict | None = None

    # @model_validator(mode="after")
    # def _coerce_settings(self) -> "PeerConfig":
    #     comp = _COMPONENT_REGISTRY.get(self.component)
    #     if comp is None:
    #         raise ValueError(
    #             f"Unknown component '{self.component}'. "
    #             f"Registered: {sorted(_COMPONENT_REGISTRY)}"
    #         )

    #     driver_name = comp.driver

    #     if driver_name is None:
    #         if self.settings not in (None, {}):
    #             raise ValueError(
    #                 f"Component '{self.component}' has no driver — "
    #                 "settings must be empty."
    #             )
    #         self.settings = None
    #         return self

    #     settings_cls: Type[BaseModel] = _DRIVER_REGISTRY[driver_name].Settings

    #     match self.settings:
    #         case None:
    #             self.settings = settings_cls()
    #         case dict():
    #             self.settings = settings_cls.model_validate(self.settings)
    #         case _ if isinstance(self.settings, settings_cls):
    #             pass  
    #         case _:
    #             raise ValueError(
    #                 f"settings must be a dict or {settings_cls.__name__} instance, "
    #                 f"got {type(self.settings).__name__!r}"
    #             )

    #     return self
    



class SetupConfig(BaseModel):
    name: str | None = None
    network: NetworkConfig | None = None
    devices: list[str] = Field(default_factory=list)  
    peers: list[PeerConfig] = Field(default_factory=list)


# ── Root ──────────────────────────────────────────────────────────────────────



class Config(BaseModel):
    devices: list[AnyDevice]
    components: list[AnyComponent]
    setups: list[SetupConfig]

@lru_cache
def get_config(path, components_path: str) -> Config:
    print("Reading config...")
    with open(path) as f:
        raw = f.read()
    
    resolved = Template(raw).substitute(components_path=components_path)
    data = yaml.safe_load(resolved)
    return Config(**data)