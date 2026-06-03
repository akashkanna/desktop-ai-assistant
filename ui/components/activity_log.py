"""Recent activity log panel."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors
from ui.components.base import GlassCard, SectionHeader

CATEGORY_COLORS = {
    "voice": Colors.NEON_BLUE,
    "gesture": Colors.NEON_PURPLE,
    "system": Colors.NEON_CYAN,
    "workflow": Colors.NEON_ORANGE,
    "ai": Colors.NEON_GREEN,
}


class ActivityLogPanel(GlassCard):
    def __init__(self):
        super().__init__(radius=16)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("Recent Activity"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self.container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self.container)
        layout.addWidget(scroll, stretch=1)

        self._empty = QLabel("No activity yet")
        self._empty.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        self._list_layout.insertWidget(0, self._empty)

    def add_entry(self, entry):
        if self._empty.isVisible():
            self._empty.hide()

        row = QFrame()
        row.setMinimumHeight(52)
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        accent = CATEGORY_COLORS.get(entry.category, Colors.NEON_BLUE)
        row.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_INPUT};
                border-radius: 10px;
            }}
        """)
        outer = QHBoxLayout(row)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        stripe = QFrame()
        stripe.setFixedWidth(4)
        stripe.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        stripe.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        outer.addWidget(stripe)

        content = QVBoxLayout()
        content.setContentsMargins(12, 8, 10, 8)
        content.setSpacing(4)

        top = QLabel(f"{entry.icon}  {entry.timestamp}  ·  {entry.category.upper()}")
        top.setWordWrap(True)
        top.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700;")
        msg = QLabel(entry.message)
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        msg.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 12px;")
        content.addWidget(top)
        content.addWidget(msg)
        outer.addLayout(content, stretch=1)

        self._list_layout.insertWidget(0, row)

    def load_entries(self, entries):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget() and item.widget() is not self._empty:
                item.widget().deleteLater()
        if not entries:
            self._empty.show()
            return
        self._empty.hide()
        for entry in entries:
            self.add_entry(entry)
