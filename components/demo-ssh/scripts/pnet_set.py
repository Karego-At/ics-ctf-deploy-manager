#!/usr/bin/env python3
"""
PROFINET DCP device management tool.

Usage:
    sudo python pnet_set.py <interface> <mac> <command> [args...]

Commands:
    factory-reset
    set-ip <ip> <subnet> <gateway> [--temporary]
    set-name <name> [--temporary]
    blink

Examples:
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF factory-reset
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF set-ip 192.168.0.50 255.255.255.0 192.168.0.1
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF set-ip 192.168.0.50 255.255.255.0 192.168.0.1 --temporary
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF set-name plc-station-1
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF set-name plc-station-1 --temporary
    sudo python pnet_set.py eth0 AA:BB:CC:DD:EE:FF blink
"""

import sys
import socket
import struct
import fcntl
from pnio_dcp import DCP


def get_local_ip(interface: str) -> str:
    SIOCGIFADDR = 0x8915
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        ifreq = struct.pack("16sH14s", interface.encode(), socket.AF_INET, b"\x00" * 14)
        result = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, ifreq)
        return socket.inet_ntoa(result[20:24])


def check(result, action: str):
    if result:
        print(f"OK: {action} — {result.get_message()}")
    else:
        print(f"FAILED: {action} — {result.get_message()}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    interface, mac, command = sys.argv[1], sys.argv[2], sys.argv[3]
    rest = sys.argv[4:]

    local_ip = get_local_ip(interface)
    dcp = DCP(ip=local_ip)

    if command == "factory-reset":
        check(dcp.factory_reset(mac), "factory reset")

    elif command == "set-ip":
        if len(rest) < 3:
            print("Usage: set-ip <ip> <subnet> <gateway> [--temporary]")
            sys.exit(1)
        ip, subnet, gateway = rest[0], rest[1], rest[2]
        permanent = "--temporary" not in rest
        check(dcp.set_ip_address(mac, [ip, subnet, gateway], store_permanent=permanent), "set-ip")

    elif command == "set-name":
        if len(rest) < 1:
            print("Usage: set-name <name> [--temporary]")
            sys.exit(1)
        name = rest[0]
        permanent = "--temporary" not in rest
        check(dcp.set_name_of_station(mac, name, store_permanent=permanent), "set-name")

    elif command == "blink":
        check(dcp.blink(mac), "blink")

    else:
        print(f"Unknown command: '{command}'")
        print(f"Available: factory-reset, set-ip, set-name, blink")
        sys.exit(1)