

import nmap 

import socket
import struct
import fcntl
import ipaddress



def get_local_network(interface: str) -> tuple[ipaddress.IPv4Network, ipaddress.IPv4Address]:

    SIOCGIFADDR    = 0x8915
    SIOCGIFNETMASK = 0x891B

    def ioctl_ip(iface: str, sioc_code: int) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            ifreq = struct.pack("16sH14s", iface.encode(), socket.AF_INET, b"\x00" * 14)
            result = fcntl.ioctl(sock.fileno(), sioc_code, ifreq)
            return socket.inet_ntoa(result[20:24])

    ip_address = ioctl_ip(interface, SIOCGIFADDR)
    netmask     = ioctl_ip(interface, SIOCGIFNETMASK)

    network = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)
    return network, ipaddress.IPv4Address(ip_address)


def arp_scan(network: ipaddress.IPv4Network) -> list[dict]:

    scanner = nmap.PortScanner()

    scanner.scan(
        hosts=str(network),
        arguments="-sn -PR --send-eth",
        # sudo=True,
    )

    devices = []
    for host in scanner.all_hosts():
        host_info = scanner[host]
        if host_info.state() != "up":
            continue

        mac = ""
        vendor = ""
        if "mac" in host_info.get("addresses", {}):
            mac = host_info["addresses"]["mac"]
            vendor = host_info.get("vendor", {}).get(mac, "")

        devices.append({
            "ip":     host,
            "mac":    mac,
            "vendor": vendor,
        })

    devices.sort(key=lambda d: ipaddress.IPv4Address(d["ip"]))
    return devices



import ipaddress
from pnio_dcp import DCP

def dcp_scan(ip, timeout: int = 10) -> list[dict]:

    # dcp = DCP(ip=str(network.network_address))
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





def s7_scan(devices: list[dict]) -> list[dict]:

    if not devices:
        return []

    scanner = nmap.PortScanner()

    # Передаём все IP одним вызовом для скорости
    hosts = " ".join(d["ip"] for d in devices)

    scanner.scan(
        hosts=hosts,
        ports="102",
        arguments="--script s7-info",
    )

    # Индексируем исходные устройства по IP чтобы не терять mac/name
    devices_by_ip = {d["ip"]: d for d in devices}

    s7_devices = []
    for host in scanner.all_hosts():
        host_info = scanner[host]

        # Порт 102 должен быть открыт
        try:
            port_info = host_info["tcp"][102]
        except KeyError:
            continue

        if port_info["state"] != "open":
            continue

        # Данные из скрипта s7-info
        script_output = port_info.get("script", {}).get("s7-info", "")
        s7_info = parse_s7_info(script_output)

        device = {**devices_by_ip.get(host, {"ip": host}), **s7_info}
        s7_devices.append(device)

    return s7_devices


def parse_s7_info(raw: str) -> dict:

    fields = {
        "Module":               "module",
        "Basic Hardware":       "hardware",
        "Version":              "firmware",
        "System Name":          "system_name",
        "Module Type":          "module_type",
        "Serial Number":        "serial_number",
        "Plant Identification": "plant_id",
        "Copyright":            "copyright",
    }

    result = {}
    for line in raw.splitlines():
        for label, key in fields.items():
            if line.strip().startswith(label + ":"):
                value = line.split(":", 1)[-1].strip()
                result[key] = value
                break

    return result




def find_plcs(s7_devices: list[dict]) -> list[dict]:
    """
    Фильтрует S7-устройства, оставляя только PLC.
    """
    PLC_KEYWORDS = ("CPU", "CP")

    return [
        d for d in s7_devices
        if any(kw in d.get("module_type", "").upper() for kw in PLC_KEYWORDS)
    ]


def find_hmis(s7_devices: list[dict]) -> list[dict]:
    """
    Фильтрует S7-устройства, оставляя только HMI.
    """
    HMI_KEYWORDS = ("HMI", "TP", "KP", "MP", "COMFORT", "BASIC", "MOBILE")

    return [
        d for d in s7_devices
        if any(kw in d.get("module_type", "").upper() for kw in HMI_KEYWORDS)
    ]