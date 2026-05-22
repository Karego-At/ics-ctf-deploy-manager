from src.test import run_pn_dev
import os
from src.config import get_config
from ipaddress import IPv4Address




path = os.getcwd()

components_path = os.path.join(path, "components")
dev_path = os.path.join(components_path, "pnet-dev")

print(path)

# run_pn_dev(dev_path)

conf_path = "./config/config.yaml"

conf = get_config(conf_path)

print(conf)

a = subfolders = [ f for f in os.scandir(components_path) if f.is_dir() and f.name == "pnet-dev"]
b = subfolders = [ f for f in os.scandir(components_path) if f.is_dir() and f.name == "attacker-ssh"]

print(type(a[0]))


nic = conf.devices[0].nic
print(type(nic))



from docker.models.images import Image
import docker

client = docker.from_env()






from docker.models.networks import Network as DockerNetwork
from docker.models.containers import Container
from src.config import PLC


class Component():
    image:  Image
    path:   str
    name:   str

    def __init__(self, path):
        self.path = path
        image, logs = client.images.build(path = path)
        self.image = image



# class DockerPeer():
#     name: str
#     container: Container
#     network: DockerNetwork

#     def __init__(self, container:Container, network:DockerNetwork, external_network = False):
#         self.container = container
#         self.network = network
#         if external_network :


        
class ConnectablePeer():

    name: str
    container: Container
    networks: list[DockerNetwork] = []
    externalNetwork: DockerNetwork


    def __init__(self, name: str, image: Image):#, ip: IPv4Address):

        self.externalNetwork = client.networks.create(name + "_external_network", driver="bridge")

        # networking_config=client.api.create_networking_config({
        # "my_network": client.api.create_endpoint_config(
        #     ipv4_address=ip
        # )
        # })


        container = client.containers.run(
        image=image.id, 
        name=name,
        network=self.externalNetwork.name,
        detach=True,
        ports={'22': 2020},  
        # networking_config = networking_config,  
        remove= True
        )
        self.container = container
            
    def destroy(self):
        self.container.kill()
        self.container.remove()
        self.externalNetwork.remove()




class MCVNetwork:
    network:    DockerNetwork
    docker_devices:     list[Container] = []
    hw_device:  PLC
    name: str

    def __init__(self, name:str, device:PLC):
        self.hw_device = device
        self.name = name
        ipam_pool = docker.types.IPAMPool(
        subnet=  str(device.nw),
        gateway='192.168.101.100',
        iprange='192.168.101.0/24'
        ) 
        ipam_config = docker.types.IPAMConfig(
            driver='default',
            pool_configs=[ipam_pool]
        )
        self.network = client.networks.create(name, driver="macvlan", options={"parent": device.nic}, ipam=ipam_config)
    

    def add_device(self, name:str, image:Image, ip:IPv4Address):


        networking_config=client.api.create_networking_config({
        "my_network": client.api.create_endpoint_config(
            ipv4_address=ip
        )
        })



        container = client.containers.run(
            image=image.id, 
            name=name,
            network=self.network.name,
            detach=True,
            networking_config = networking_config,  
            remove= True
             
        )
        self.docker_devices.append(container)
        return container

    def connect(self, peer:ConnectablePeer):
        peer.networks.append(self.network)
        # self.docker_devices.append(peer.container)
        self.network.connect(peer.container)


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

nw.add_device(name="hw-sens-man", image=comp1.image, ip="192.168.101.1")



print(conf.devices[0].nw)





comp2 = Component(b[0].path)

attacker = ConnectablePeer("attacker", comp2.image)

nw.connect(attacker)


input()

nw.destruct()

attacker.destroy()