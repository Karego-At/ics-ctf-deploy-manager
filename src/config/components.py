from __future__ import annotations
from pydantic import BaseModel, model_validator, Field, field_validator
from typing import Any, Literal, Annotated, Union, Type, ClassVar
import os, re


# _DRIVER_REGISTRY: dict[str, Type[BaseDriver]] = {}

# class BaseDriver:
#     name: ClassVar[str]

#     def __init_subclass__(cls, **kwargs: Any) -> None: 
#         super().__init_subclass__(**kwargs)
#         if n := getattr(cls, "name", None):
#             _DRIVER_REGISTRY[n] = cls

#     # class Settings(BaseModel):
#     #     pass

# # # ── Concrete drivers ──────────────────────────────────────────────────────────

# class PnetDriver(BaseDriver):
#     name = "pnet-driver"

#     # class Settings(BaseModel):
#     #     interface: str | None = None
#     #     vlan: int | None = None
#     #     mtu: int = 1500





# ── Components ────────────────────────────────────────────────────────────────

class ComponentConfig(BaseModel):
    type: Literal["simple"] = "simple"
    name: str
    path: str
    driver: str | None = None


class ConnectableComponentConfig(ComponentConfig):
    type: Literal["connectable"] = "connectable"
    port: int


AnyComponent = Annotated[
    Union[ConnectableComponentConfig, ComponentConfig],
    Field(discriminator="type"),
]


