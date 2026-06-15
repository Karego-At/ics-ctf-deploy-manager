import docker
from docker.models.networks import Network as DockerNetwork
from src.model.components.components import Peer
import logging
from docker.errors import NotFound, APIError
from src.model.utils import suffix_generator

logger = logging.getLogger(__name__)

client = docker.from_env()


class BaseNetwork:
    def __init__(self, name: str, driver: str,
                 options: dict | None = None,
                 ipam: dict | None = None,
                 args: dict | None = None):
        if name:
            self.name = name
        else:
            network_suffix = suffix_generator() # random.randint(1000, 9999)
            self.name = f"internal_network_{network_suffix}"
        self.driver = driver
        self.peers: list[Peer] = []

        if ipam:
            ipam_pool = docker.types.IPAMPool(**ipam)
            ipam_config = docker.types.IPAMConfig(
                driver="default",
                pool_configs=[ipam_pool],
            )
        else:
            ipam_config = None



        logger.debug("create network", self.driver, options, ipam)

        self.network = client.networks.create(
            name = self.name,
            driver=self.driver,
            options=options,
            ipam=ipam_config,
            **(args or {})
        )

    def add_peer(self, peer: Peer):
        self.peers.append(peer)


    def start(self) -> None:
        errors: list[Exception] = []
        started: list[Peer] = []

        for peer in self.peers:
            try:
                peer.start()
                started.append(peer)
                logger.info("Peer %s started.", peer)
            except RuntimeError as e:
                logger.error("Error starting peer %s: %s", peer, e)
                errors.append(e)

                logger.warning("Rolling back %d started peer(s)...", len(started))
                for s in reversed(started):
                    try:
                        s.destroy()
                        logger.info("Rolled back peer %s.", s)
                    except RuntimeError as rollback_err:
                        logger.error("Rollback failed for peer %s: %s", s, rollback_err)
                break

        if errors:
            raise RuntimeError(
                f"Network.start() failed: {errors}. All started peers have been rolled back."
            )

    def destroy(self) -> None:
        errors: list[Exception] = []

        for peer in self.peers:
            try:
                peer.destroy()
                logger.info("Peer %s destroyed.", peer)
            except RuntimeError as e:
                logger.error("Error destroying peer %s: %s", peer, e)
                errors.append(e)

        try:
            self.network.reload()
            self.network.remove()
            logger.info("Network %r removed.", self.name)
        except NotFound:
            logger.warning("Network %r already gone (remove skipped).", self.name)
        except APIError as e:
            logger.error("Error removing network %r: %s", self.name, e)
            errors.append(e)

        if errors:
            raise RuntimeError(
                f"Network.destroy() finished with {len(errors)} error(s): {errors}"
            )
    

    

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r}>"


# class MacVlanNetwork(BaseNetwork):
#     def __init__(self, name: str, parent: str,
#                  args: dict | None = None):
#         merged_args = {"options": {"parent": parent}, **(args or {})}  
#         super().__init__(name, driver="macvlan", args=merged_args)
#         self.parent = parent


# class BridgeNetwork(BaseNetwork):
#     def __init__(self, name: str, **network_args):
#         super().__init__(name, driver="bridge", **network_args)



# class MCVNetwork:
#     network:    DockerNetwork
#     docker_devices:     list[Container] = []
#     hw_device:  PlcConfig
#     name: str

#     def __init__(self, name:str, device:PlcConfig):
#         self.hw_device = device
#         self.name = name
#         ipam_pool = docker.types.IPAMPool(
#         subnet=  str(device.nw),
#         gateway='192.168.101.100',
#         iprange='192.168.101.0/24'
#         ) 
#         ipam_config = docker.types.IPAMConfig(
#             driver='default',
#             pool_configs=[ipam_pool]
#         )
#         self.network = client.networks.create(name, driver="macvlan", options={"parent": device.nic}, ipam=ipam_config)


#     def add_device(self, name:str, image:Image, ip:IPv4Address):


#         networking_config=client.api.create_networking_config({
#         "my_network": client.api.create_endpoint_config(
#             ipv4_address=ip
#         )
#         })



#         container = client.containers.run(
#             image=image.id, 
#             name=name,
#             network=self.network.name,
#             detach=True,
#             networking_config = networking_config,  
#             remove= True
             
#         )
#         self.docker_devices.append(container)
#         return container

#     def connect(self, peer:Connectable):
#         peer.networks.append(self.network)
#         # self.docker_devices.append(peer.container)
#         self.network.connect(peer.container)


#     def destruct(self):
#         print("self destruction")
#         for cont in self.docker_devices:
#             cont.kill()
#             cont.remove()
#         self.network.remove()