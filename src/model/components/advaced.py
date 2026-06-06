

from base import Driver, Component, Peer

from docker.models.networks import Network as DockerNetwork
from src.config.options import ConnectionOptions, RunOptions


from src.model.components.base import Peer
import tarfile
import io



import logging
import random
import socket
from contextlib import suppress

import docker
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network as DockerNetwork

from src.config.options import ConnectionOptions, RunOptions





logger = logging.getLogger(__name__)

client = docker.from_env()



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
        
        


    class ConnectablePeer(Peer):


        def __init__(
            self,
            component: Component,
            network: DockerNetwork,
            network_options: ConnectionOptions,
            run_options: RunOptions,
            # network_options: dict | None = None,
            # run_options: dict | None = None,
            host_port: int | None = None,   
        ):
            network_suffix = random.randint(1000, 9999)
            self.external_network: DockerNetwork = client.networks.create(
                f"external_network_{network_suffix}", driver="bridge"
            )


            self.host_port = host_port or get_first_free_port()
            additional_options = {"ports": {component.config.port: self.host_port}}

            super().__init__(
                component,
                self.external_network,
                network_options=None,   
                run_options=run_options,
                **additional_options
            )
            network.connect(
                self.container,
                **(network_options.to_kwargs() if network_options else {})
            )

            self.network = network


        def destroy(self) -> None:

            errors: list[Exception] = []

            try:
                self.network.disconnect(self.container, force=True)
                logger.info(
                    "Container %s disconnected from internal network %s.",
                    self.container.short_id,
                    self.network.name,
                )
            except NotFound:
                logger.warning(
                    "Container %s or internal network not found — disconnect skipped.",
                    self.container.short_id,
                )
            except APIError as e:
                logger.error(
                    "Error disconnecting container %s from internal network: %s",
                    self.container.short_id,
                    e,
                )
                errors.append(e)

            try:
                super().destroy()
            except RuntimeError as e:
                errors.append(e)

            try:
                self.external_network.remove()
                logger.info("External network %s removed.", self.external_network.name)
            except NotFound:
                logger.warning("External network %s already removed.", self.external_network.name)
            except APIError as e:
                logger.error("Error removing external network %s: %s", self.external_network.name, e)
                errors.append(e)

            if errors:
                raise RuntimeError(
                    f"ConnectablePeer.destroy() finished with {len(errors)} error(s): {errors}"
                )


    _PEERS: dict[str, type[Peer]] = {
        "connectable": ConnectablePeer,
        "simple": Peer,
    }


    def create_peer(
        component: Component,
        network: DockerNetwork,
        connection_options: dict | None = None,
        run_options: dict | None = None,
        **kwargs
    ) -> Peer:
        peer_cls = _PEERS.get(component.type)
        if peer_cls is None:
            raise ValueError(f"Unknown component type: {component.type}")
        return peer_cls(component, network, network_options=connection_options, run_options=run_options, **kwargs)






_DRIVERS: dict[str, type[Driver]] = {
    "pnet-driver": PnetDriver,
    "attacker-ssh-driver": Driver,
}


def get_driver(
    driver:str
) -> Driver:
    cls = _DRIVERS.get(driver)
    if cls is None:
        raise ValueError(f"Unknown driver: {driver}")
    return cls

