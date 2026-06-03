"""Thread-safe system metrics polling."""

import platform
import socket
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, Signal

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class SystemMetrics:
    cpu: float = 0.0
    ram: float = 0.0
    disk: float = 0.0
    gpu: float = 0.0
    net_connected: bool = True
    mic_available: bool = True
    camera_available: bool = True
    assistant_health: float = 100.0
    os_name: str = "Windows"
    cpu_name: str = "Unknown CPU"
    ram_total_gb: float = 0.0
    uptime: str = "—"


class SystemMonitorService(QObject):
    metrics_updated = Signal(object)

    def __init__(self, parent=None, interval_ms: int = 2000):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._poll)
        self._static_loaded = False
        self._static = {}

    def start(self):
        self._load_static()
        self._poll()
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def _load_static(self):
        if self._static_loaded:
            return
        self._static_loaded = True
        self._static["os_name"] = f"{platform.system()} {platform.release()}"
        if psutil:
            self._static["cpu_name"] = platform.processor() or "CPU"
            self._static["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        else:
            self._static["cpu_name"] = platform.processor() or "CPU"
            self._static["ram_total_gb"] = 0.0

    def _poll(self):
        m = SystemMetrics(
            os_name=self._static.get("os_name", "Windows"),
            cpu_name=self._static.get("cpu_name", "CPU"),
            ram_total_gb=self._static.get("ram_total_gb", 0.0),
            net_connected=self._check_network(),
            mic_available=True,
            camera_available=True,
            assistant_health=100.0,
            uptime=self._uptime(),
        )
        if psutil:
            m.cpu = psutil.cpu_percent(interval=None)
            m.ram = psutil.virtual_memory().percent
            try:
                m.disk = psutil.disk_usage("/").percent if platform.system() != "Windows" else psutil.disk_usage("C:\\").percent
            except Exception:
                m.disk = 0.0
        self.metrics_updated.emit(m)

    def _check_network(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5).close()
            return True
        except OSError:
            return False

    def _uptime(self) -> str:
        if not psutil:
            return "—"
        try:
            boot = psutil.boot_time()
            import time
            secs = int(time.time() - boot)
            h, rem = divmod(secs, 3600)
            m, _ = divmod(rem, 60)
            return f"{h}h {m}m"
        except Exception:
            return "—"
