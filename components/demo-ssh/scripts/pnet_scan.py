#!/usr/bin/env python3
import sys
import ipaddress
import socket
import struct
import fcntl
from pnio_dcp import DCP


def get_local_network(interface: str) -> tuple[ipaddress.IPv4Network, ipaddress.IPv4Address]:
    SIOCGIFADDR    = 0x8915
    SIOCGIFNETMASK = 0x891B

    def ioctl_ip(iface: str, sioc_code: int) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            ifreq = struct.pack("16sH14s", iface.encode(), socket.AF_INET, b"\x00" * 14)
            result = fcntl.ioctl(sock.fileno(), sioc_code, ifreq)
            return socket.inet_ntoa(result[20:24])

    ip_address = ioctl_ip(interface, SIOCGIFADDR)
    netmask    = ioctl_ip(interface, SIOCGIFNETMASK)
    network    = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)
    return network, ipaddress.IPv4Address(ip_address)


def dcp_scan(ip, timeout: int = 10) -> list[dict]:
    dcp = DCP(ip=ip)
    devices = []
    for d in dcp.identify_all(timeout=timeout):
        devices.append({
            "ip":   d.IP,
            "mac":  d.MAC,
            "name": d.name_of_station,
        })
    devices.sort(key=lambda d: ipaddress.IPv4Address(d["ip"]))
    return devices


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <interface>")
        sys.exit(1)

    interface = sys.argv[1]
    _, local_ip = get_local_network(interface)
    devices = dcp_scan(str(local_ip))

    for d in devices:
        print(f"{d['ip']}\t{d['mac']}\t{d['name']}")