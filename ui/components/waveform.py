"""Animated audio waveform visualization."""

from typing import Iterable

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush

from ui.theme.theme_manager import Colors


class WaveformWidget(QWidget):
    """Horizontal bar waveform for live microphone energy."""

    def __init__(self, bar_count: int = 24, parent=None):
        super().__init__(parent)
        self._bars = [0.0] * bar_count
        self._active = False
        self._level_pct = 0
        self.setMinimumHeight(20)
        self.setMaximumHeight(28)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def set_active(self, active: bool):
        self._active = active
        if not active:
            self._bars = [0.0] * len(self._bars)
            self._level_pct = 0
            self.update()

    def set_levels(self, levels: Iterable[float], level_pct: float = 0.0):
        if not self._active:
            return

        if len(levels) != len(self._bars):
            levels = list(levels)[: len(self._bars)]
            levels += [0.0] * (len(self._bars) - len(levels))

        for i, target in enumerate(levels):
            target = max(0.0, min(1.0, target))
            self._bars[i] += (target - self._bars[i]) * 0.24

        self._level_pct = int(round(max(0.0, min(100.0, level_pct))))
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

        if self._level_pct > 0:
            p.setPen(QColor(Colors.TEXT_MUTED))
            p.drawText(w - 56, 12, f"{self._level_pct}%")
        p.end()
