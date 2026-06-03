"""Feature capability cards grid — responsive columns."""

from PySide6.QtWidgets import QFrame, QGridLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors
from ui.components.base import GlassCard, SectionHeader
from ui.layout.responsive import Breakpoints


FEATURES = [
    ("🎙", "Voice Assistant", "Natural language commands & wake word detection", "voice"),
    ("✋", "Gesture Recognition", "MediaPipe hand tracking for cursor control", "gesture"),
    ("▦", "Window Management", "Snap, minimize, maximize active windows", "apps"),
    ("⚙", "System Control", "Volume, power, lock, and sleep actions", "system"),
    ("📷", "Screenshot Capture", "Instant desktop capture engine", "screenshots"),
    ("🧠", "AI Memory", "Short & long-term preference storage", "memory"),
    ("⚡", "Workflow Engine", "Multi-step automation sequences", "workflow"),
    ("🚀", "App Launcher", "Launch apps and websites instantly", "apps"),
]


class FeatureCard(GlassCard):
    clicked = Signal(str)

    def __init__(self, icon: str, title: str, desc: str, page_key: str):
        super().__init__(radius=14, glow=True)
        self.page_key = page_key
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(88)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-size: 12px; font-weight: 800;"
        )
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.page_key)
        super().mousePressEvent(event)


class FeaturesPanel(QFrame):
    feature_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(SectionHeader("Features"))

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        self._cards = []
        for icon, title, desc, key in FEATURES:
            card = FeatureCard(icon, title, desc, key)
            card.clicked.connect(self.feature_selected.emit)
            self._cards.append(card)
        layout.addWidget(self._grid_host)
        self._cols = 2
        self._relayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cols = 1 if self.width() < 340 else 2
        if cols != self._cols:
            self._cols = cols
            self._relayout()

    def _relayout(self):
        while self._grid.count():
            self._grid.takeAt(0)
        for i, card in enumerate(self._cards):
            self._grid.addWidget(card, i // self._cols, i % self._cols)
