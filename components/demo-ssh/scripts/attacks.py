
import discovery as d

from pnio_dcp import DCP

TIMEOUT = 10


def dcp_destroy():


    interface = INTERFACE
    network, ip = d.get_local_network(interface)
    s_ip = str(ip)

    pnet_devs = d.dcp_scan(s_ip, TIMEOUT)

    dcp = DCP(ip=s_ip)

    for dev in pnet_devs():
        DCP.reset_to_factory(dcp, dev.get("mac"))
