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
from src.config.components import ComponentConfig


# from src.model.components.advanced import Driver, get_driver

logger = logging.getLogger(__name__)

client = docker.from_env()



def get_first_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]




class Component:
    def __init__(self, config: ComponentConfig):
        self.config = config
        self.name = config.name
        self.path = config.path
        self.type = config.type
        self.driver = config.driver
        self.image = self._build()
        # self.instances: list[Container] = []

    def _build(self) -> Image:
        image, _logs = client.images.build(path=self.path)
        return image







class Peer:
    def __init__(
        self,
        component: Component,
        network: DockerNetwork,
        # network_options: NetworkOptions,
        # run_options: RunOptions,
        network_options: ConnectionOptions,
        run_options: RunOptions,
        driver: Driver = None,
        **kwargs
    ):
        self.network = network
        self.component = component
        networking_config = {
            self.network.name: client.api.create_endpoint_config(
                **(network_options.to_kwargs() if network_options else {})
            )
        }
        self.container = client.containers.create(
            image=self.component.image.id,
            network=self.network.name,
            networking_config=networking_config,
            **run_options.to_kwargs(),
            **kwargs
        )
        self.driver = get_driver(component.driver) if component.driver else None


    def start(self) -> None:
        try:
            self.container.start()
            logger.info("Container %s started.", self.container.short_id)
        except NotFound:
            logger.error("Container %s not found — already removed?", self.container.short_id)
            raise
        except APIError as e:
            logger.error("Failed to start container %s: %s", self.container.short_id, e)
            raise

    

    def configure(self, **kwargs):
        if self.driver is None:
            logger.info("No driver configured for container %s, skipping configure.", self.container.short_id)
            return
        self.driver.configure(self, **kwargs)



    def destroy(self) -> None:

        errors: list[Exception] = []

        try:
            self.container.reload()       
            if self.container.status == "running":
                self.container.stop(timeout=10)
                logger.info("Container %s stopped.", self.container.short_id)
        except NotFound:
            logger.warning("Container %s already gone (stop skipped).", self.container.short_id)
        except APIError as e:
            logger.error("Error stopping container %s: %s", self.container.short_id, e)
            errors.append(e)

        try:
            self.container.remove(force=True)
            logger.info("Container %s removed.", self.container.short_id)
        except NotFound:
            logger.warning("Container %s already removed.", self.container.short_id)
        except APIError as e:
            logger.error("Error removing container %s: %s", self.container.short_id, e)
            errors.append(e)

        if errors:
            raise RuntimeError(
                f"Peer.destroy() finished with {len(errors)} error(s): {errors}"
            )
        # network.connect(self.container)





class Driver:
    def __init__(self):
        pass

    def configure(self, peer: "Peer", data: str):
        pass






