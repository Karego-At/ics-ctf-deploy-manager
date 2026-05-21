from src.test import run_pn_dev
import os
from src.config import get_config

path = os.getcwd()

components_path = os.path.join(path, "components")
dev_path = os.path.join(components_path, "pnet-dev")

print(path)

# run_pn_dev(dev_path)

conf_path = "./config/config.yaml"

conf = get_config(conf_path)

print(conf)

a = subfolders = [ f for f in os.scandir(components_path) if f.is_dir() and f.name == "pnet-dev"]
print(type(a[0]))


from docker.models.images import Image
import docker

client = docker.from_env()


class Component():
    image:  Image
    path:   str
    name:   str

    def __init__(self, path):
        self.path = path
        image, logs = client.images.build(path = path)
        self.image = image



from docker.models.networks import Network as DockerNetwork
from docker.models.containers import Container
from src.config import PLC

class MCVNetwork:
    network:    DockerNetwork
    docker_devices:     list[Container] = []
    hw_device:  PLC
    name: str

    def __init__(self, name:str, device:PLC):
        self.hw_device = device
        self.name = name
        ipam_pool = docker.types.IPAMPool(
        subnet= device.nw
        # gateway='192.168.101.1',
        # iprange='192.168.101.192/28'
        ) 
        ipam_config = docker.types.IPAMConfig(
            driver='default',
            pool_configs=[ipam_pool]
        )
        self.network = client.networks.create(name, driver="macvlan", options={"parent": device.nic})#, ipam=ipam_config)
    

    def add_device(self, name:str, comp:Component):
        container = client.containers.run(
            image=comp.image.id, 
           # name=name,
            network=self.network.name,
            detach=True
        )
        self.docker_devices.append(container)
        return container
    
    def destruct(self):
        print("self destruction")
        for cont in self.docker_devices:
            cont.kill()
            cont.remove()
        self.network.remove()


    # def __exit__(self, exc_type, exc, tb):
    #     self.destruct()
    
    # def __delete__(self, instance):
    #     self.destruct()

    # def __del__(self):
    #     self.destruct()



comp1 = Component(a[0].path)

nw = MCVNetwork("nw3", conf.devices[0])

nw.add_device(name="hw-sens-man", comp=comp1)








# nw.destruct()