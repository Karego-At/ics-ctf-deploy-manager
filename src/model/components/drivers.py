
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.model.components.components import Peer


import tarfile
import io
import json
import yaml




class Driver:
    def __init__(self):
        pass

    def _make_tar_archive(self, filename: str, content: bytes) -> io.BytesIO:
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            info = tarfile.TarInfo(name=filename)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        tar_stream.seek(0)
        return tar_stream

    def _put_file(self, peer: Peer, filename: str, content: bytes, path: str = "/"):
        tar_stream = self._make_tar_archive(filename, content)
        peer.container.put_archive(path=path, data=tar_stream)

    def configure(self, peer: Peer):
        pass


class PnetDriver(Driver):
    def __init__(self, **kwargs):
        super().__init__()

    def configure(self, peer: Peer, data: str):
        content = data.encode("utf-8")
        self._put_file(peer, "flag.txt", content, path="/")


class SshDriver(Driver):
    def configure(self, peer: Peer, users: list = None):
        if not users:
            return

        content = json.dumps({"users": users}).encode("utf-8")
        self._put_file(peer, "users-setup.json", content, path="/ws")


class AttackerDriver(Driver):
    pass



class HMIDriver(Driver):
    PATH = "/app/config"
    OUTPUT_FILE = "output_config.yaml"
    CONNECTION_FILE = "connection_config.yaml"

    def _put_yaml(self, peer: Peer, filename: str, data: dict) -> None:
        content = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        ).encode("utf-8")
        self._put_file(peer, filename, content, path=self.PATH)

    def configure(self, peer: Peer,
                  output_settings: dict = None,
                  connection_settings: dict = None) -> None:
        if output_settings:
            self._put_yaml(peer, self.OUTPUT_FILE, output_settings)
        if connection_settings:
            self._put_yaml(peer, self.CONNECTION_FILE, connection_settings)



    
_DRIVERS: dict[str, type[Driver]] = {
    "pnet-driver": PnetDriver,
    "ssh-driver": SshDriver,
    "attacker-driver" : AttackerDriver,
    "hmi-driver": HMIDriver
}



def get_driver(driver: str | None) -> Driver | None:
    if driver is None:
        return None
    cls = _DRIVERS.get(driver)
    if cls is None:
        raise ValueError(f"Unknown driver: {driver}")
    return cls() 