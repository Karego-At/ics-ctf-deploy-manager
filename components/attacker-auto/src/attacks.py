
import discovery as d

from pnio_dcp import DCP



def dcp_destroy(interface: str):

    TIMEOUT = 10

    network, ip = d.get_local_network(interface)


    pnet_devs = d.dcp_scan(ip, TIMEOUT)

    dcp = DCP(ip=ip)

    for dev in pnet_devs():
        dcp.reset_to_factory(dev.mac)













