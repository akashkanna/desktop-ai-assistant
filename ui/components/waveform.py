"""Animated audio waveform visualization."""

import math
import random

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush

from ui.theme.theme_manager import Colors


class WaveformWidget(QWidget):
    """Horizontal bar waveform for listening/speaking states."""

    def __init__(self, bar_count: int = 24, parent=None):
        super().__init__(parent)
        self._bars = [0.15] * bar_count
        self._active = False
        self._tick = 0.0
        self.setMinimumHeight(20)
        self.setMaximumHeight(28)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._timer.start()
        else:
            self._timer.stop()
            self._bars = [0.12] * len(self._bars)
            self.update()

    def _on_tick(self):
        self._tick += 0.08
        for i in range(len(self._bars)):
            if self._active:
                self._bars[i] = 0.15 + abs(math.sin(self._tick * 4 + i * 0.45)) * 0.85
            else:
                self._bars[i] = 0.12
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setClipRect(self.rect())
        w, h = self.width(), self.height()
        n = len(self._bars)
        gap = 3
        bar_w = max(2, (w - gap * (n - 1)) // n)

        for i, frac in enumerate(self._bars):
            bar_h = max(4, frac * (h - 4))
            x = i * (bar_w + gap)
            y = (h - bar_h) / 2
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor(Colors.NEON_BLUE))
            grad.setColorAt(1, QColor(Colors.NEON_PURPLE))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(int(x), int(y), bar_w, int(bar_h), 2, 2)
        p.end()
