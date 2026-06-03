"""Quick action button grid — flexible sizing."""

from PySide6.QtWidgets import (
    QFrame, QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QWidget,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors
from ui.components.base import GlassCard, SectionHeader


ACTIONS = [
    ("🚀", "Open App", "open_app", Colors.NEON_BLUE),
    ("📷", "Screenshot", "screenshot", Colors.NEON_PURPLE),
    ("🔒", "Lock", "lock", Colors.NEON_PINK),
    ("⏻", "Shutdown", "shutdown", Colors.NEON_ORANGE),
    ("🔄", "Restart", "restart", Colors.NEON_CYAN),
    ("🔊", "Vol Up", "vol_up", Colors.NEON_BLUE),
    ("🔉", "Vol Down", "vol_down", Colors.NEON_PURPLE),
    ("🌐", "Browser", "browser", Colors.NEON_GREEN),
]


class QuickActionButton(QPushButton):
    def __init__(self, icon: str, label: str, action: str, color: str):
        super().__init__(f"{icon}\n{label}")
        self.action_key = action
        self._color = color
        self.setMinimumSize(56, 56)
        self.setMaximumSize(80, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 28px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 9px;
                font-weight: 700;
                padding: 4px;
            }}
            QPushButton:hover {{
                border-color: {self._color};
                background-color: {self._color}22;
            }}
        """)


class QuickActionsPanel(GlassCard):
    action_triggered = Signal(str)

    def __init__(self):
        super().__init__(radius=16)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(SectionHeader("Quick Actions"))

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setSpacing(8)
        self._buttons = []
        for icon, label, key, color in ACTIONS:
            btn = QuickActionButton(icon, label, key, color)
            btn.clicked.connect(lambda checked=False, k=key: self.action_triggered.emit(k))
            self._buttons.append(btn)
        layout.addWidget(self._grid_host)
        self._cols = 4
        self._relayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        cols = 4 if w >= 360 else (3 if w >= 280 else 2)
        if cols != self._cols:
            self._cols = cols
            self._relayout()

    def _relayout(self):
        while self._grid.count():
            self._grid.takeAt(0)
        for i, btn in enumerate(self._buttons):
            self._grid.addWidget(btn, i // self._cols, i % self._cols)
