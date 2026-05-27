
from pydantic import BaseModel, model_validator, Field
from typing import Literal, Annotated, Union
from ipaddress import IPv4Interface




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
