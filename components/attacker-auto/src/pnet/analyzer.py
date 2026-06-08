# analyzer.py
import queue
import threading
import struct
from datetime import datetime
from scapy.all import sniff
from scapy.layers.l2 import Ether

PROFINET_ETHERTYPE = 0x8892
SENTINEL = None  # сигнал завершения


# ─── Layer 1: захват ──────────────────────────────────────────────────────────

class Sniffer(threading.Thread):
    """Только захватываетырые пакеты и кладёт в очередь."""

    def __init__(self, raw_queue: queue.Queue, interface="eth0" ):
        super().__init__(daemon=True)
        self.raw_queue = raw_queue
        self.interface = interface
        # self.timeout   = timeout or None
        # self.count     = count or 0

    def run(self):
        sniff(
            iface=self.interface,
            prn=self.raw_queue.put,  # просто кладём сырой пакет
            # timeout=self.timeout,
            # count=self.count,
            store=False,
        )
        self.raw_queue.put(SENTINEL)  # говорим downstream'у, что закончили


# ─── Layer 2: диссектор ───────────────────────────────────────────────────────

class Dissector(threading.Thread):
    """Читает сырые пакеты, парсит, кладёт структуры в следующую очередь."""

    def __init__(self, raw_queue: queue.Queue, parsed_queue: queue.Queue):
        super().__init__(daemon=True)
        self.raw_queue    = raw_queue
        self.parsed_queue = parsed_queue

    def run(self):
        while True:
            pkt = self.raw_queue.get()
            if pkt is SENTINEL:
                self.parsed_queue.put(SENTINEL)
                break

            parsed = self._dissect(pkt)
            if parsed:
                self.parsed_queue.put(parsed)

    def _dissect(self, pkt) -> dict | None:
        if not pkt.haslayer(Ether):
            return None
        if pkt[Ether].type != PROFINET_ETHERTYPE:
            return None

        raw = bytes(pkt[Ether].payload)
        if len(raw) < 4:
            return None

        frame_id = struct.unpack(">H", raw[:2])[0]
        return {
            "timestamp":  datetime.now().isoformat(),
            "src_mac":    pkt[Ether].src,
            "dst_mac":    pkt[Ether].dst,
            "frame_id":   hex(frame_id),
            "frame_type": classify_frame_id(frame_id),
            "payload":    raw[2:].hex(),
            "length":     len(raw),
        }


# ─── Layer 3: бизнес-логика ───────────────────────────────────────────────────

class Analyzer(threading.Thread):
    """
    Читает распарсенные пакеты и выполняет высокоуровневую логику.
    Сюда добавляешь алерты, статистику, запись в БД — что угодно.
    """

    def __init__(self, parsed_queue: queue.Queue):
        super().__init__(daemon=True)
        self.parsed_queue = parsed_queue
        self.results: list[dict] = []

        # Регистр обработчиков: frame_type → [handler, ...]
        self._handlers: dict[str, list] = {}
        # Глобальные обработчики (на любой пакет)
        self._global_handlers: list = []

    # --- публичный API --------------------------------------------------------

    def on(self, frame_type: str):
        """Декоратор: вызывать функцию при конкретном типе фрейма."""
        def decorator(fn):
            self._handlers.setdefault(frame_type, []).append(fn)
            return fn
        return decorator

    def on_any(self, fn):
        """Вызывать функцию на каждый пакет."""
        self._global_handlers.append(fn)
        return fn

    # --- внутренняя логика ----------------------------------------------------

    def run(self):
        while True:
            pkt = self.parsed_queue.get()
            if pkt is SENTINEL:
                break
            self.results.append(pkt)
            self._dispatch(pkt)

    def _dispatch(self, pkt: dict):
        for fn in self._global_handlers:
            fn(pkt)
        for fn in self._handlers.get(pkt["frame_type"], []):
            fn(pkt)


# ─── Точка входа ─────────────────────────────────────────────────────────────

def run_pipeline(interface="eth0") -> list[dict]:
    raw_q    = queue.Queue()
    parsed_q = queue.Queue()

    sniffer   = Sniffer(raw_q, interface=interface)
    dissector = Dissector(raw_q, parsed_q)
    analyzer  = Analyzer(parsed_q)

    # Регистрируем бизнес-логику
    @analyzer.on("ALARM_HIGH")
    def on_alarm(pkt):
        print(f"[ALERT] ALARM_HIGH от {pkt['src_mac']} в {pkt['timestamp']}")

    @analyzer.on_any
    def log_all(pkt):
        print(f"[PKT] {pkt['frame_type']:30s} | {pkt['src_mac']} → {pkt['dst_mac']}")

    sniffer.start()
    dissector.start()
    analyzer.start()

    # Ждём завершения всего пайплайна
    sniffer.join()
    dissector.join()
    analyzer.join()

    return analyzer.results