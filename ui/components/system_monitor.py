"""Real-time system monitor with circular gauges."""

import math

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from ui.theme.theme_manager import Colors
from ui.components.base import GlassCard, SectionHeader


GAUGE_COLORS = {
    "cpu": Colors.NEON_BLUE,
    "ram": Colors.NEON_PURPLE,
    "disk": Colors.NEON_CYAN,
    "net": Colors.NEON_GREEN,
}


class CircularGauge(QWidget):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0.0
        self.setFixedSize(64, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value: float):
        self._value = max(0.0, min(100.0, value))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, 36
        r = 28

        p.setPen(QPen(QColor(Colors.BORDER), 6))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        pen = QPen(QColor(self._color), 6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        span = int(360 * 16 * (self._value / 100.0))
        p.drawArc(cx - r, cy - r, r * 2, r * 2, 90 * 16, -span)

        p.setPen(QColor(Colors.TEXT_PRIMARY))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(0, cy - 8, w, 20, Qt.AlignCenter, f"{int(self._value)}%")

        p.setPen(QColor(Colors.TEXT_MUTED))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(0, h - 18, w, 16, Qt.AlignCenter, self._label)
        p.end()


class SystemMonitorPanel(GlassCard):
    def __init__(self):
        super().__init__(radius=16, glow=True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(SectionHeader("System Monitor"))

        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(8)
        self.cpu_gauge = CircularGauge("CPU", GAUGE_COLORS["cpu"])
        self.ram_gauge = CircularGauge("RAM", GAUGE_COLORS["ram"])
        self.disk_gauge = CircularGauge("DISK", GAUGE_COLORS["disk"])
        self.net_gauge = CircularGauge("NET", GAUGE_COLORS["net"])
        for g in (self.cpu_gauge, self.ram_gauge, self.disk_gauge, self.net_gauge):
            gauge_row.addWidget(g)
        layout.addLayout(gauge_row)

        self.specs = QLabel("Loading system info…")
        self.specs.setWordWrap(True)
        self.specs.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px; line-height: 1.4;")
        layout.addWidget(self.specs)

        status_grid = QGridLayout()
        status_grid.setSpacing(6)
        self.mic_status = QLabel("🎤 Mic: Available")
        self.cam_status = QLabel("📷 Camera: Available")
        self.net_status = QLabel("🌐 Network: Connected")
        self.health_status = QLabel("💚 Health: 100%")
        for i, lbl in enumerate((self.mic_status, self.cam_status, self.net_status, self.health_status)):
            lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
            status_grid.addWidget(lbl, i // 2, i % 2)
        layout.addLayout(status_grid)

    def update_metrics(self, metrics):
        self.cpu_gauge.set_value(metrics.cpu)
        self.ram_gauge.set_value(metrics.ram)
        self.disk_gauge.set_value(metrics.disk)
        self.net_gauge.set_value(12.0 if metrics.net_connected else 0.0)
        self.specs.setText(
            f"OS: {metrics.os_name}\n"
            f"CPU: {metrics.cpu_name}\n"
            f"RAM: {metrics.ram_total_gb} GB\n"
            f"Uptime: {metrics.uptime}"
        )
        self.mic_status.setText(f"🎤 Mic: {'Available' if metrics.mic_available else 'Unavailable'}")
        self.cam_status.setText(f"📷 Camera: {'Available' if metrics.camera_available else 'Unavailable'}")
        self.net_status.setText(f"🌐 Network: {'Connected' if metrics.net_connected else 'Offline'}")
        self.health_status.setText(f"💚 Health: {int(metrics.assistant_health)}%")
