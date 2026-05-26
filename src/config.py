from pydantic import BaseModel, model_validator, Field
from typing import Literal, Annotated, Union
from ipaddress import IPv4Interface
from functools import lru_cache
import yaml
from string import Template



# ── Devices ──────────────────────────────────────────────────────────────────

class DeviceConfig(BaseModel):
    name: str | None = None
    type: Literal["Device"]
    nw: IPv4Interface
    nic: str

    @model_validator(mode="after")
    def check_device_availability(self):
        return self



class PlcConfig(DeviceConfig):
    type: Literal["PLC"]


AnyDevice = Annotated[
    Union[PlcConfig, DeviceConfig],
    Field(discriminator="type")
]


# ── Components ────────────────────────────────────────────────────────────────

class ComponentConfig(BaseModel):
    type: Literal["simple"] = "simple"
    name: str
    path: str


class ConnectableComponentConfig(ComponentConfig):
    type: Literal["connectable"] = "connectable"
    port: int

AnyComponent = Annotated[
    Union[ConnectableComponentConfig, ComponentConfig],
    Field(discriminator="type")
]


# ── Connection / Run options ──────────────────────────────────────────────────

class ConnectionOptions(BaseModel):
    aliases: list[str] = Field(default_factory=list)
    ipv4_address: str | None = None
    # ipv6_address: str | None = None
    # link_local_ips: list[str] = Field(default_factory=list)
    # driver_opt: dict[str, str] = Field(default_factory=dict)
    mac_address: str | None = None

    def to_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True, exclude_defaults=True)


class RunOptions(BaseModel):
    # ports: dict[int, int] = Field(default_factory=dict)
    # volumes: dict[str, VolumeMount] = Field(default_factory=dict)
    # tmpfs: dict[str, str] = Field(default_factory=dict)  # {"/run": "size=64m"}
    # environment: dict[str, str] = Field(default_factory=dict)
    # command: str | list[str] | None = None
    # entrypoint: str | list[str] | None = None
    # working_dir: str | None = None
    # user: str | None = None

    mem_limit: str | None = None        # "512m", "1g"
    memswap_limit: str | None = None
    cpu_period: int | None = None
    cpu_quota: int | None = None
    cpu_shares: int | None = None

    # restart_policy: RestartPolicy | None = None
    # privileged: bool = False
    # cap_add: list[str] = Field(default_factory=list)   # ["NET_ADMIN"]
    # cap_drop: list[str] = Field(default_factory=list)
    # devices: list[str] = Field(default_factory=list)   # ["/dev/ttyUSB0:/dev/ttyUSB0"]
    # sysctls: dict[str, str] = Field(default_factory=dict)

    log_config: dict | None = None

    def to_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True, exclude_defaults=True)
        if "volumes" in data:
            data["volumes"] = {k: v for k, v in data["volumes"].items()}
        return data


# ── Setups ────────────────────────────────────────────────────────────────────

class NetworkConfig(BaseModel):
    name: str | None = None
    type: str
    # ipam: dict | None = None
    # params: dict | None = None


class PeerConfig(BaseModel):
    name: str | None = None
    component: str            
    connection_options: ConnectionOptions = Field(default_factory=ConnectionOptions)
    run_options: RunOptions = Field(default_factory=RunOptions)


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