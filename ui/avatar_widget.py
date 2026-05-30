"""
Jarvis Animated Avatar Widget — drawn with QPainter.
Features: idle pulsing glow, listening waveform, speaking bounce, thinking orbit.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QLinearGradient, QPen, QBrush, QFont, QPainterPath
import math
import time


class AvatarWidget(QWidget):
    """Animated circular AI avatar that reacts to assistant states."""

    STATES = ("idle", "listening", "thinking", "speaking")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._state = "idle"
        self._tick = 0.0           # continuous time counter for animations
        self._wave_bars = [0.0] * 12   # bar heights for listening waveform
        self._speaking_amp = 0.0   # amplitude for speaking bounce

        # Animation driver — 30fps
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    # ──────────────────────────────────── public API ────
    def set_state(self, state: str):
        if state in self.STATES:
            self._state = state

    # ──────────────────────────────────── animation tick ────
    def _on_tick(self):
        self._tick += 0.05
        if self._state == "listening":
            import random
            for i in range(len(self._wave_bars)):
                self._wave_bars[i] = abs(math.sin(self._tick * 3 + i * 0.6)) * 0.7 + 0.3
        elif self._state == "speaking":
            self._speaking_amp = 0.5 + 0.5 * abs(math.sin(self._tick * 5))
        self.update()

    # ──────────────────────────────────── painting ────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 10

        t = self._tick

        # ── Background glow ──────────────────────────────
        self._draw_glow(p, cx, cy, r, t)

        # ── Outer ring ──────────────────────────────────
        self._draw_outer_ring(p, cx, cy, r, t)

        # ── Core circle ─────────────────────────────────
        self._draw_core(p, cx, cy, r * 0.68)

        # ── State-specific decoration ────────────────────
        if self._state == "listening":
            self._draw_waveform(p, cx, cy, r * 0.45)
        elif self._state == "thinking":
            self._draw_orbit(p, cx, cy, r, t)
        elif self._state == "speaking":
            self._draw_speaking_rings(p, cx, cy, r * 0.68, t)
        else:
            self._draw_idle_pulse(p, cx, cy, r, t)

        # ── Face icon ────────────────────────────────────
        self._draw_face(p, cx, cy, r * 0.45, t)

        p.end()

    def _draw_glow(self, p, cx, cy, r, t):
        pulse = 0.4 + 0.15 * math.sin(t)
        gradient = QRadialGradient(QPointF(cx, cy), r * 1.4)
        if self._state == "listening":
            c = QColor(30, 150, 255, int(80 * pulse))
        elif self._state == "speaking":
            c = QColor(160, 80, 255, int(90 * pulse))
        elif self._state == "thinking":
            c = QColor(255, 180, 30, int(70 * pulse))
        else:
            c = QColor(80, 200, 160, int(60 * pulse))
        gradient.setColorAt(0, c)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(gradient))
        p.drawEllipse(QPointF(cx, cy), r * 1.4, r * 1.4)

    def _draw_outer_ring(self, p, cx, cy, r, t):
        pen = QPen()
        pen.setWidth(3)
        if self._state == "listening":
            alpha = int(200 + 55 * math.sin(t * 4))
            pen.setColor(QColor(30, 150, 255, alpha))
        elif self._state == "speaking":
            alpha = int(200 + 55 * math.sin(t * 6))
            pen.setColor(QColor(160, 80, 255, alpha))
        elif self._state == "thinking":
            alpha = int(200 + 55 * math.sin(t * 3))
            pen.setColor(QColor(255, 180, 30, alpha))
        else:
            alpha = int(160 + 40 * math.sin(t))
            pen.setColor(QColor(80, 200, 160, alpha))
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Dashed accent ring
        pen2 = QPen(pen.color().lighter(130), 1, Qt.DashLine)
        p.setPen(pen2)
        p.drawEllipse(QPointF(cx, cy), r * 0.82, r * 0.82)

    def _draw_core(self, p, cx, cy, r):
        gradient = QRadialGradient(QPointF(cx, cy - r * 0.2), r * 1.2)
        gradient.setColorAt(0.0, QColor(40, 44, 60))
        gradient.setColorAt(0.6, QColor(22, 24, 38))
        gradient.setColorAt(1.0, QColor(12, 14, 24))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(gradient))
        p.drawEllipse(QPointF(cx, cy), r, r)

    def _draw_idle_pulse(self, p, cx, cy, r, t):
        # Soft concentric pulsing rings
        for i in range(3):
            phase = t - i * 0.8
            scale = 1.05 + 0.12 * abs(math.sin(phase * 0.8))
            alpha = int(60 * abs(math.sin(phase * 0.8)))
            pen = QPen(QColor(80, 200, 160, alpha), 1)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r * scale * (1.1 + i * 0.12),
                          r * scale * (1.1 + i * 0.12))

    def _draw_waveform(self, p, cx, cy, r):
        n = len(self._wave_bars)
        bar_w = 5
        total_w = n * (bar_w + 3)
        x0 = cx - total_w / 2

        for i, h_frac in enumerate(self._wave_bars):
            bar_h = max(4, h_frac * r * 0.9)
            x = x0 + i * (bar_w + 3)
            y = cy - bar_h / 2

            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor(30, 180, 255, 220))
            grad.setColorAt(1, QColor(100, 80, 255, 180))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 3, 3)

    def _draw_thinking_dots(self, p, cx, cy, r, t):
        for i in range(3):
            angle = t * 2 + i * (2 * math.pi / 3)
            dx = math.cos(angle) * r * 0.55
            dy = math.sin(angle) * r * 0.55
            alpha = int(200 + 55 * math.sin(t * 3 + i))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 180, 30, alpha))
            p.drawEllipse(QPointF(cx + dx, cy + dy), 6, 6)

    def _draw_orbit(self, p, cx, cy, r, t):
        # Orbiting dot
        for i in range(3):
            angle = t * 2.5 + i * (2 * math.pi / 3)
            orb_r = r * 0.88
            dx = math.cos(angle) * orb_r
            dy = math.sin(angle) * orb_r
            size = 5 + 3 * math.sin(t * 3 + i)
            alpha = int(200 + 55 * math.sin(t * 4 + i))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 180, 30, alpha))
            p.drawEllipse(QPointF(cx + dx, cy + dy), size, size)

    def _draw_speaking_rings(self, p, cx, cy, r, t):
        amp = self._speaking_amp
        for i in range(4):
            scale = 1.0 + (i + 1) * 0.08 * amp
            alpha = int(80 - i * 18)
            pen = QPen(QColor(160, 80, 255, alpha), 2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r * scale, r * scale)

    def _draw_face(self, p, cx, cy, r, t):
        # Robot eyes
        eye_y = cy - r * 0.12
        eye_gap = r * 0.32
        eye_r  = r * 0.14
        blink  = abs(math.sin(t * 0.4)) > 0.97

        if self._state == "listening":
            eye_color = QColor(30, 180, 255)
        elif self._state == "speaking":
            eye_color = QColor(180, 80, 255)
        elif self._state == "thinking":
            eye_color = QColor(255, 200, 30)
        else:
            eye_color = QColor(80, 220, 160)

        for dx in (-eye_gap, eye_gap):
            ex, ey = cx + dx, eye_y
            grad = QRadialGradient(QPointF(ex, ey), eye_r)
            grad.setColorAt(0, eye_color.lighter(160))
            grad.setColorAt(1, eye_color)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            if blink:
                p.drawEllipse(QPointF(ex, ey), eye_r, 2)
            else:
                p.drawEllipse(QPointF(ex, ey), eye_r, eye_r)
            # Pupil
            p.setBrush(QColor(10, 10, 20, 200))
            p.drawEllipse(QPointF(ex, ey), eye_r * 0.4, eye_r * 0.4)

        # Mouth
        mouth_y = cy + r * 0.32
        if self._state == "speaking":
            mouth_h = r * 0.18 * self._speaking_amp
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(180, 80, 255, 180))
            p.drawEllipse(QPointF(cx, mouth_y), r * 0.22, max(4, mouth_h))
        else:
            pen = QPen(eye_color, 2, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            path = QPainterPath()
            path.moveTo(cx - r * 0.22, mouth_y)
            path.cubicTo(cx - r * 0.1, mouth_y + r * 0.12,
                         cx + r * 0.1, mouth_y + r * 0.12,
                         cx + r * 0.22, mouth_y)
            p.drawPath(path)
