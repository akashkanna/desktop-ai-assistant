"""In-memory activity feed for the dashboard."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from PySide6.QtCore import QObject, Signal


@dataclass
class ActivityEntry:
    timestamp: str
    category: str
    message: str
    icon: str = "•"


class ActivityLogService(QObject):
    entry_added = Signal(object)
    log_cleared = Signal()

    CATEGORIES = ("voice", "gesture", "system", "workflow", "ai")

    def __init__(self, parent=None, max_entries: int = 100):
        super().__init__(parent)
        self._entries: List[ActivityEntry] = []
        self._max = max_entries

    def log(self, message: str, category: str = "system", icon: str = "•"):
        entry = ActivityEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            category=category,
            message=message,
            icon=icon,
        )
        self._entries.insert(0, entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[: self._max]
        self.entry_added.emit(entry)

    def entries(self) -> List[ActivityEntry]:
        return list(self._entries)

    def clear(self):
        self._entries.clear()
        self.log_cleared.emit()
