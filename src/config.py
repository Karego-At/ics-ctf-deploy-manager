from pydantic import BaseModel, model_validator

from typing import Literal
from ipaddress import IPv4Interface
from functools import lru_cache
import yaml






class PLC(BaseModel):
    type: Literal["PLC"]
    name: str
    nw: IPv4Interface
    nic: str

    @model_validator(mode="after")
    def check_device_availability(self):
        return self






class Config(BaseModel):
    devices : list[PLC]



@lru_cache
def get_config(path) -> Config:
    print("Reading config...") 
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(**data)


