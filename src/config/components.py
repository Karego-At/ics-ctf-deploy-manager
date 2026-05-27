from __future__ import annotations
from pydantic import BaseModel, model_validator, Field, field_validator
from typing import Any, Literal, Annotated, Union, Type, ClassVar
import os, re

# ── Driver registry ───────────────────────────────────────────────────────────

_DRIVER_REGISTRY: dict[str, Type[BaseDriver]] = {}

_COMPONENT_REGISTRY: dict[str, AnyComponent] = {}


def register_component(c: AnyComponent) -> AnyComponent:
    _COMPONENT_REGISTRY[c.name] = c
    return c



class BaseDriver:
    name: ClassVar[str]

    class Settings(BaseModel):
        pass

    # def __init_subclass__(cls, **kwargs: Any) -> None:
    #     super().__init_subclass__(**kwargs)
    #     if n := getattr(cls, "name", None):
    #         _DRIVER_REGISTRY[n] = cls


# ── Concrete drivers ──────────────────────────────────────────────────────────

class PnetDriver(BaseDriver):
    name = "pnet-driver"

    class Settings(BaseModel):
        interface: str | None = None
        vlan: int | None = None
        mtu: int = 1500





# ── Components ────────────────────────────────────────────────────────────────

class ComponentConfig(BaseModel):
    type: Literal["simple"] = "simple"
    name: str
    path: str
    driver: str | None = None

    # @field_validator("driver")
    # @classmethod
    # def _check_driver(cls, v: str | None) -> str | None:
    #     if v is not None and v not in _DRIVER_REGISTRY:
    #         raise ValueError(
    #             f"Unknown driver '{v}'. "
    #             f"Registered: {sorted(_DRIVER_REGISTRY)}"
    #         )
    #     return v



class ConnectableComponentConfig(ComponentConfig):
    type: Literal["connectable"] = "connectable"
    port: int


AnyComponent = Annotated[
    Union[ConnectableComponentConfig, ComponentConfig],
    Field(discriminator="type"),
]


