




from src.config.devices import AnyDevice
# ComponentConfig, ConnectionOptions, RunOptions, AnyDevice

from src.model.components import Component, create_peer
from src.model.networks import BaseNetwork
from src.config.loader import SetupConfig


import logging

logger = logging.getLogger(__name__)
        

        


class Manager:


    def __init__(self, components:list[Component], devices: list[AnyDevice]):
        self.components = components
        self.devices = devices
        self.networks:list[BaseNetwork] = []


    def create_setup(self, config: SetupConfig):

        try:
            nw_conf = config.network
            if len(config.devices) > 1:
                raise NotImplementedError  
    
            if len(config.devices) == 1:
                device = next(d for d in self.devices if d.name == config.devices[0]) 
                options = {"parent": device.nic}
                ipam = {"subnet": str(device.nw)}
            else:
            
                options = {}
                ipam = {}
    
            network = BaseNetwork(name=nw_conf.name, driver=nw_conf.driver, options=options, ipam=ipam)
    
            self.networks.append(network) 
            
            for p in config.peers:
                comp = next(c for c in self.components if c.name == p.component)  
                peer = create_peer(component=comp, 
                                   network=network.network,
                                   connection_options=p.connection_options,
                                   run_options=p.run_options, 
                                   **(p.args or {}))
                network.add_peer(peer)
        except Exception as e:
            self.destroy()
            print(e)
        
    
    def start(self):
        for network in self.networks:
            network.start()


    def destroy(self):
        errors: list[Exception] = []

        for network in self.networks:
            try:
                network.destroy()
                logger.info("Network %r destroyed.", network.name)
            except RuntimeError as e:
                logger.error("Error destroying network %r: %s", network.name, e)
                errors.append(e)

        if errors:
            raise RuntimeError(
                f"Manager.destroy() finished with {len(errors)} error(s): {errors}"
            )
        

        




