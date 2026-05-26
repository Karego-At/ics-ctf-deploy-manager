from src.test import run_pn_dev
import os
from src.config import get_config
from src.model.components import Component
from ipaddress import IPv4Address
import sys

from src.config import ComponentConfig, ConnectionOptions, RunOptions
from src.model.manager import Manager


path = os.getcwd()
conf_path = "./config/config.yaml"
components_path = os.path.join(path, "components")


def main():
    conf = get_config(conf_path, components_path)
    devices = conf.devices
    components = [Component(c) for c in conf.components]
    manager = Manager(components=components, devices=devices)

    for s in conf.setups:
        manager.create_setup(config=s)

    manager.networks[0].start()

    manager.destroy()

    return



if __name__ == '__main__':
    sys.exit(main())






# a = subfolders = [ f for f in os.scandir(components_path) if f.is_dir() and f.name == "pnet-dev"]
# b = subfolders = [ f for f in os.scandir(components_path) if f.is_dir() and f.name == "attacker-ssh"]

# print(type(a[0]))


# nic = conf.devices[0].nic
# print(type(nic))



# from docker.models.images import Image
# import docker

# client = docker.from_env()






# class DockerPeer():
#     name: str
#     container: Container
#     network: DockerNetwork

#     def __init__(self, container:Container, network:DockerNetwork, external_network = False):
#         self.container = container
#         self.network = network
#         if external_network :



        
# class Connectable():
#     name: str
#     container: Container
#     networks: list[DockerNetwork] = []
#     externalNetwork: DockerNetwork


#     def __init__(self, name: str, image: Image):#, ip: IPv4Address):

#         self.externalNetwork = client.networks.create(name + "_external_network", driver="bridge")

#         # networking_config=client.api.create_networking_config({
#         # "my_network": client.api.create_endpoint_config(
#         #     ipv4_address=ip
#         # )
#         # })


#         container = client.containers.run(
#         image=image.id, 
#         name=name,
#         network=self.externalNetwork.name,
#         detach=True,
#         ports={'22': 2020},  
#         # networking_config = networking_config,  
#         remove= True
#         )
#         self.container = container
            
#     def destroy(self):
#         self.container.kill()
#         self.container.remove()
#         self.externalNetwork.remove()







#     # def __exit__(self, exc_type, exc, tb):
#     #     self.destruct()
    
#     # def __delete__(self, instance):
#     #     self.destruct()

#     # def __del__(self):
#     #     self.destruct()



# comp1 = Component(a[0].path)


# nw = MCVNetwork("nw3", conf.devices[0])

# nw.add_device(name="hw-sens-man", image=comp1.image, ip="192.168.101.1")



# print(conf.devices[0].nw)





# comp2 = Component(b[0].path)

# attacker = Connectable("attacker", comp2.image)

# nw.connect(attacker)


# input()

# nw.destruct()

# attacker.destroy()