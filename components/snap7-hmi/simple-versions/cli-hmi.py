"""
Custom S7Comm HMI — reads IB20-IB29 (10 bytes) from the PLC input area.
Bytes correspond to a custom PROFINET device that outputs "Hello World".

Data layout example:
  IB20-IB29 -> 10 ASCII characters = "Hello Worl" (or full string if device
  sends only the relevant characters)

Dependencies:  pip install python-snap7 rich
"""

import time
import datetime
import snap7
from snap7.type import Areas
from snap7.util import get_bool
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box

# ─────────────────────────────────────────────
#  Connection configuration
# ─────────────────────────────────────────────
PLC_IP   = "192.168.1.55"   # <- replace with the real PLC IP
RACK     = 0
SLOT     = 1
TCP_PORT = 102

# Read range: IB20 ... IB29
START_BYTE = 20          # first byte (IB20)
BYTE_COUNT = 10          # number of bytes (IB20-IB29)

POLL_INTERVAL = 1.0      # seconds between polls

console = Console()


# ─────────────────────────────────────────────
#  Helper functions
# ─────────────────────────────────────────────

def connect_plc() -> snap7.Client:
    """Creates and returns a connected Snap7 client."""
    client = snap7.Client()
    client.connect(address=PLC_IP, rack=RACK, slot=SLOT, tcp_port=TCP_PORT)
    return client


def read_input_bytes(client: snap7.Client,
                     start: int = START_BYTE,
                     count: int = BYTE_COUNT) -> bytearray:
    """
    Reads `count` bytes from the Process Inputs area (PE), starting at byte `start`.
    Uses Areas.PE (Process Inputs) — corresponds to IB addresses in TIA Portal.

    read_area(area, db_number, start, size)
    db_number = 0 for PE / PA / MK / TM / CT
    """
    raw: bytearray = client.read_area(
        area      = Areas.PE,   # PE = Process Inputs (IB...)
        db_number = 0,
        start     = start,
        size      = count,
    )
    return raw


def decode_hello_world(data: bytearray) -> str:
    """
    Decodes 10 bytes as an ASCII string.
    Non-printable characters are replaced with a middle dot (hex-dump style).
    """
    chars = ""
    for b in data:
        chars += chr(b) if 0x20 <= b <= 0x7E else "·"
    return chars


def decode_bits(byte_val: int) -> str:
    """Returns an 8-bit string representation (MSB to LSB)."""
    return format(byte_val, "08b")


# ─────────────────────────────────────────────
#  Rich table builder
# ─────────────────────────────────────────────

def build_table(data: bytearray, timestamp: str, connected: bool) -> Table:
    status_color = "green" if connected else "red"
    status_text  = "● ONLINE" if connected else "● OFFLINE"

    table = Table(
        title=(
            f"[bold cyan]S7Comm HMI  |  PROFINET -> IB{START_BYTE}-IB{START_BYTE + BYTE_COUNT - 1}[/bold cyan]"
            f"   [{status_color}]{status_text}[/{status_color}]   "
            f"[dim]{timestamp}[/dim]"
        ),
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )

    table.add_column("Address",         style="bold yellow", justify="center", width=8)
    table.add_column("HEX",             style="cyan",        justify="center", width=6)
    table.add_column("DEC",             style="white",       justify="right",  width=5)
    table.add_column("Bits (MSB->LSB)", style="dim green",   justify="center", width=12)
    table.add_column("ASCII",           style="bold green",  justify="center", width=6)

    for i, byte_val in enumerate(data):
        addr  = f"IB{START_BYTE + i}"
        hex_s = f"0x{byte_val:02X}"
        dec_s = str(byte_val)
        bits  = decode_bits(byte_val)
        char  = chr(byte_val) if 0x20 <= byte_val <= 0x7E else "·"
        table.add_row(addr, hex_s, dec_s, bits, char)

    return table


def build_hello_panel(data: bytearray) -> Panel:
    message = decode_hello_world(data)
    # Strip trailing null / placeholder bytes if string is shorter than 10 chars
    clean = message.rstrip("·").rstrip("\x00")
    return Panel(
        f"[bold white on blue]  {clean}  [/bold white on blue]",
        title="[bold]Message from PROFINET device[/bold]",
        border_style="blue",
        expand=False,
    )


# ─────────────────────────────────────────────
#  Main HMI loop
# ─────────────────────────────────────────────

def run_hmi():
    console.print(
        Panel(
            "[bold cyan]S7Comm Custom HMI[/bold cyan]\n"
            f"Connecting to PLC [yellow]{PLC_IP}[/yellow]  "
            f"rack=[yellow]{RACK}[/yellow]  slot=[yellow]{SLOT}[/yellow]  "
            f"port=[yellow]{TCP_PORT}[/yellow]\n"
            f"Read range: [green]IB{START_BYTE} - IB{START_BYTE + BYTE_COUNT - 1}[/green]  "
            f"([cyan]{BYTE_COUNT} bytes[/cyan])\n\n"
            "[dim]Press Ctrl+C to quit[/dim]",
            title="Settings",
            border_style="cyan",
        )
    )

    client: snap7.Client | None = None

    def get_client() -> snap7.Client | None:
        nonlocal client
        try:
            if client is None or not client.get_connected():
                client = connect_plc()
                console.print(f"[green]Connected to {PLC_IP}[/green]")
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
            client = None
        return client

    with Live(console=console, refresh_per_second=4) as live:
        while True:
            now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            c = get_client()

            if c and c.get_connected():
                try:
                    data  = read_input_bytes(c)
                    table = build_table(data, now, connected=True)
                    hello = build_hello_panel(data)
                    from rich.console import Group
                    live.update(Group(table, hello))

                except Exception as e:
                    live.update(
                        Panel(f"[red]Read error: {e}[/red]", title="Error")
                    )
                    client = None
            else:
                placeholder = bytearray(BYTE_COUNT)
                build_table(placeholder, now, connected=False)
                live.update(
                    Panel(
                        f"[red]PLC unreachable ({PLC_IP}).  Retrying in {POLL_INTERVAL:.0f} s...[/red]",
                        title="No connection",
                        border_style="red",
                    )
                )

            time.sleep(POLL_INTERVAL)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run_hmi()
    except KeyboardInterrupt:
        console.print("\n[yellow]HMI stopped by user.[/yellow]")