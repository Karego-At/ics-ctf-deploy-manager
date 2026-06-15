from scapy.all import sniff, Raw
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
import struct
from datetime import datetime


PROFINET_ETHERTYPE = 0x8892


def parse_pnet_packet(pkt) -> dict | None:
    """
    parse raw Profinet pkt. Return None if not profinet pkt.
    """
    if not pkt.haslayer(Ether):
        return None
    if pkt[Ether].type != PROFINET_ETHERTYPE:
        return None

    raw = bytes(pkt[Ether].payload)
    if len(raw) < 4:
        return None

    frame_id = struct.unpack(">H", raw[:2])[0]

    return {
        "timestamp": datetime.now().isoformat(),
        "src_mac":   pkt[Ether].src,
        "dst_mac":   pkt[Ether].dst,
        "frame_id":  hex(frame_id),
        "frame_type": classify_frame_id(frame_id),
        "payload":   raw[2:].hex(),
        "length":    len(raw),
    }


def classify_frame_id(frame_id: int) -> str:
    if 0x0020 <= frame_id <= 0x001F:
        return "PTCP (Time Sync)"
    elif 0x0100 <= frame_id <= 0x7FFF:
        return "RTC3 (IRT - Isochronous Real Time)"
    elif 0x8000 <= frame_id <= 0xBFFF:
        return "RTC2 (RT class 2)"
    elif 0xC000 <= frame_id <= 0xFBFF:
        return "RTC1 (RT class 1)"
    elif frame_id == 0xFC01:
        return "ALARM_HIGH"
    elif frame_id == 0xFE01:
        return "ALARM_LOW"
    elif 0xFF00 <= frame_id <= 0xFF1F:
        return "DCP (Discovery and Config)"
    elif 0xFF20 <= frame_id <= 0xFF3F:
        return "PTCP Announce"
    elif 0xFF40 <= frame_id <= 0xFF5F:
        return "PTCP Follow Up"
    else:
        return "Unknown"


