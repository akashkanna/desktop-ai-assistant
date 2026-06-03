"""Square quick-action cards with hover animation."""

from PySide6.QtWidgets import (
    QFrame, QGridLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget,
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, Property

from ui.theme.theme_manager import Colors
from ui.components.base import SectionHeader
from ui.themes import glass_style


ACTIONS = [
    ("🚀", "Open App", "open_app", Colors.NEON_BLUE),
    ("📷", "Screenshot", "screenshot", Colors.NEON_PURPLE),
    ("🔒", "Lock", "lock", Colors.NEON_PINK),
    ("⏻", "Shutdown", "shutdown", Colors.NEON_ORANGE),
    ("🔄", "Restart", "restart", Colors.NEON_CYAN),
    ("🌐", "Browser", "browser", Colors.NEON_GREEN),
    ("🔊", "Vol Up", "vol_up", Colors.NEON_BLUE),
    ("🔉", "Vol Down", "vol_down", Colors.NEON_PURPLE),
]


class ActionCard(QPushButton):
    def __init__(self, icon: str, label: str, action: str, accent: str):
        super().__init__()
        self.action_key = action
        self._accent = accent
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(72, 72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText(f"{icon}\n{label}")
        self._apply(False)

    def _apply(self, hover: bool):
        bg = f"{self._accent}33" if hover else "rgba(10, 20, 40, 0.55)"
        border = self._accent if hover else Colors.BORDER
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 16px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 10px;
                font-weight: 700;
                padding: 8px;
            }}
        """)

    def enterEvent(self, e):
        self._apply(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply(False)
        super().leaveEvent(e)


class QuickActionsGrid(QFrame):
    action_triggered = Signal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ {glass_style(16)} }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(SectionHeader("Quick Actions"))

        self._host = QWidget()
        self._grid = QGridLayout(self._host)
        self._grid.setSpacing(8)
        self._buttons = []
        for icon, label, key, color in ACTIONS:
            btn = ActionCard(icon, label, key, color)
            btn.clicked.connect(lambda checked=False, k=key: self.action_triggered.emit(k))
            self._buttons.append(btn)
        layout.addWidget(self._host)
        self._cols = 2
        self._relayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cols = 4 if self.width() >= 320 else (2 if self.width() >= 180 else 1)
        if cols != self._cols:
            self._cols = cols
            self._relayout()

    def _relayout(self):
        while self._grid.count():
            self._grid.takeAt(0)
        for i, btn in enumerate(self._buttons):
            self._grid.addWidget(btn, i // self._cols, i % self._cols)
