
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.model.components.components import Peer


import tarfile
import io
import json




class Driver:
    def __init__(self):
        pass

    def configure(self, peer: Peer, data: str):
        pass


class PnetDriver(Driver):
    def __init__(self, **kwargs):
        super().__init__()

    def configure(self, peer: Peer, data: str):
        content = data.encode("utf-8")

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            info = tarfile.TarInfo(name="flag.txt")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        tar_stream.seek(0)

        peer.container.put_archive(path="/", data=tar_stream)


class SshDriver(Driver):
    def configure(self, peer: Peer, users: list = None):
        if not users:
            return

        content = json.dumps({"users": users}).encode("utf-8")  # обернули в {"users": [...]}

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            info = tarfile.TarInfo(name="users-setup.json")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        tar_stream.seek(0)

        peer.container.put_archive(path="/ws", data=tar_stream)



    
_DRIVERS: dict[str, type[Driver]] = {
    "pnet-driver": PnetDriver,
    "attacker-ssh-driver": Driver,
    "ssh-driver": SshDriver,
}



def get_driver(driver: str | None) -> Driver | None:
    if driver is None:
        return None
    cls = _DRIVERS.get(driver)
    if cls is None:
        raise ValueError(f"Unknown driver: {driver}")
    return cls() 