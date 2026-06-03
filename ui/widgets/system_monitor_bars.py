"""System monitor with animated horizontal bars."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QSizePolicy, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QLinearGradient

from ui.theme.theme_manager import Colors
from ui.components.base import SectionHeader
from ui.themes import glass_style


class MetricBar(QWidget):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0.0
        self._display = 0.0
        self.setMinimumHeight(32)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._anim = QPropertyAnimation(self, b"display_value")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_display_value(self):
        return self._display

    def set_display_value(self, v):
        self._display = v
        self.update()

    display_value = Property(float, get_display_value, set_display_value)

    def set_value(self, value: float):
        self._value = max(0.0, min(100.0, value))
        self._anim.stop()
        self._anim.setStartValue(self._display)
        self._anim.setEndValue(self._value)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QColor(Colors.TEXT_SECONDARY))
        p.drawText(0, 14, self._label)
        p.setPen(QColor(Colors.TEXT_PRIMARY))
        p.drawText(w - 40, 14, f"{int(self._display)}%")

        bar_y, bar_h = 20, 10
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(Colors.BORDER))
        p.drawRoundedRect(0, bar_y, w, bar_h, 5, 5)

        fill_w = int((w * self._display) / 100.0)
        if fill_w > 0:
            grad = QLinearGradient(0, bar_y, fill_w, bar_y)
            grad.setColorAt(0, QColor(self._color))
            grad.setColorAt(1, QColor(Colors.NEON_PURPLE))
            p.setBrush(grad)
            p.drawRoundedRect(0, bar_y, fill_w, bar_h, 5, 5)
        p.end()


class SystemMonitorBars(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ {glass_style(16)} }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(SectionHeader("System Monitor"))

        self._monitor_grid = QGridLayout()
        self._monitor_grid.setContentsMargins(0, 0, 0, 0)
        self._monitor_grid.setSpacing(8)
        self.cpu_bar = MetricBar("CPU Usage", Colors.NEON_BLUE)
        self.ram_bar = MetricBar("RAM Usage", Colors.NEON_PURPLE)
        self.gpu_bar = MetricBar("GPU Usage", Colors.NEON_CYAN)
        self.disk_bar = MetricBar("Disk Usage", Colors.NEON_ORANGE)
        self.net_bar = MetricBar("Network", Colors.NEON_GREEN)
        self._bars = [self.cpu_bar, self.ram_bar, self.gpu_bar, self.disk_bar, self.net_bar]
        self._arrange_bars(2)
        layout.addLayout(self._monitor_grid)

        status = QHBoxLayout()
        self.mic_lbl = QLabel("🎤 Mic: OK")
        self.cam_lbl = QLabel("📷 Camera: OK")
        self.health_lbl = QLabel("💚 Health: 100%")
        for lbl in (self.mic_lbl, self.cam_lbl, self.health_lbl):
            lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
            status.addWidget(lbl)
        status.addStretch()
        layout.addLayout(status)

        self.specs = QLabel("")
        self.specs.setWordWrap(True)
        self.specs.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(self.specs)

    def update_metrics(self, metrics):
        self.cpu_bar.set_value(metrics.cpu)
        self.ram_bar.set_value(metrics.ram)
        self.disk_bar.set_value(metrics.disk)
        self.gpu_bar.set_value(getattr(metrics, "gpu", 0.0))
        self.net_bar.set_value(15.0 if metrics.net_connected else 0.0)
        self.mic_lbl.setText(f"🎤 Mic: {'OK' if metrics.mic_available else 'Off'}")
        self.cam_lbl.setText(f"📷 Camera: {'OK' if metrics.camera_available else 'Off'}")
        self.health_lbl.setText(f"💚 Health: {int(metrics.assistant_health)}%")
        self.specs.setText(
            f"{metrics.os_name}  ·  {metrics.cpu_name}  ·  "
            f"{metrics.ram_total_gb} GB RAM  ·  Uptime {metrics.uptime}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange_bars(1 if self.width() < 620 else 2)

    def _arrange_bars(self, columns: int):
        while self._monitor_grid.count():
            item = self._monitor_grid.takeAt(0)
            if item.widget():
                self._monitor_grid.removeWidget(item.widget())
        for idx, bar in enumerate(self._bars):
            self._monitor_grid.addWidget(bar, idx // columns, idx % columns)
