"""Activity timeline — modern vertical event stream."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors
from ui.components.base import SectionHeader
from ui.themes import glass_style

CATEGORY_META = {
    "voice": ("Voice Command", Colors.NEON_BLUE, "🎙"),
    "gesture": ("Gesture", Colors.NEON_PURPLE, "✋"),
    "system": ("System", Colors.NEON_CYAN, "⚙"),
    "workflow": ("Workflow", Colors.NEON_ORANGE, "⚡"),
    "ai": ("AI Response", Colors.NEON_GREEN, "🤖"),
}


class TimelineItem(QFrame):
    def __init__(self, entry):
        super().__init__()
        meta = CATEGORY_META.get(entry.category, ("Event", Colors.NEON_BLUE, "•"))
        title, color, icon = meta
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        rail = QVBoxLayout()
        rail.setAlignment(Qt.AlignTop)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        line = QFrame()
        line.setFixedWidth(2)
        line.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        line.setStyleSheet(f"background: {Colors.BORDER};")
        rail.addWidget(dot, alignment=Qt.AlignHCenter)
        rail.addWidget(line, stretch=1)
        outer.addLayout(rail)

        body = QVBoxLayout()
        body.setContentsMargins(12, 10, 12, 10)
        body.setSpacing(4)
        head = QLabel(f"{icon}  {title}")
        head.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 800;")
        msg = QLabel(entry.message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 12px;")
        time = QLabel(entry.timestamp)
        time.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
        body.addWidget(head)
        body.addWidget(msg)
        body.addWidget(time)
        outer.addLayout(body, stretch=1)
        self.setStyleSheet("background: rgba(15, 25, 45, 0.35); border-radius: 14px;")


class ActivityTimeline(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ {glass_style(16)} }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("Activity Timeline"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._container = QWidget()
        self._container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._list = QVBoxLayout(self._container)
        self._list.setContentsMargins(0, 0, 0, 0)
        self._list.setSpacing(10)
        self._empty = QLabel("No activity yet")
        self._empty.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px; padding: 12px;")
        self._list.addWidget(self._empty)
        self._list.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll, stretch=1)

    def add_entry(self, entry):
        if self._empty.isVisible():
            self._empty.hide()
        item = TimelineItem(entry)
        self._list.insertWidget(0, item)

    def load_entries(self, entries):
        while self._list.count() > 1:
            w = self._list.takeAt(0)
            if w.widget() and w.widget() is not self._empty:
                w.widget().deleteLater()
        if not entries:
            self._empty.show()
            return
        self._empty.hide()
        for entry in entries:
            self.add_entry(entry)
