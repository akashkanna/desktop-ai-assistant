"""Right AI Core status panel — integrations and system health."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors
from ui.components.base import SectionHeader
from ui.themes import glass_style
from services.integration_hooks import IntegrationRegistry


CORE_ITEMS = [
    ("Model", "model"),
    ("Memory", "memory"),
    ("Voice", "voice"),
    ("Gesture", "gesture"),
    ("MongoDB", "mongodb"),
    ("Ollama", "ollama"),
    ("OpenAI", "openai"),
    ("Gemini", "gemini"),
    ("System Health", "health"),
]


class StatusRow(QFrame):
    def __init__(self, label: str, online: bool = True, detail: str = "Ready"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 20, 40, 0.45);
                border-radius: 10px;
            }}
        """)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(8)
        dot_color = Colors.SUCCESS if online else Colors.TEXT_MUTED
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; font-size: 10px;")
        name = QLabel(label)
        name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 12px; font-weight: 700;")
        val = QLabel(detail)
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        row.addWidget(dot)
        row.addWidget(name)
        row.addStretch()
        row.addWidget(val)
        self._dot = dot
        self._val = val
        self._name = name

    def update(self, online: bool, detail: str):
        detail_lower = detail.lower()
        if not online or any(word in detail_lower for word in ("off", "error", "fail", "unavailable")):
            color = Colors.DANGER
        elif any(word in detail_lower for word in ("ok", "active", "ready", "%", "connected")):
            color = Colors.SUCCESS
        else:
            color = Colors.WARNING
        self._dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self._val.setStyleSheet(f"color: {color}; font-size: 10px;")
        self._val.setText(detail)


class AiCoreStatusPanel(QFrame):
    def __init__(self, registry: IntegrationRegistry | None = None):
        super().__init__()
        self.setObjectName("AiCoreStatus")
        self.setStyleSheet(f"QFrame#AiCoreStatus {{ {glass_style(18)} }}")
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self._registry = registry or IntegrationRegistry()
        self._rows: dict[str, StatusRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("AI Core"))

        for label, key in CORE_ITEMS:
            row = StatusRow(label, online=True, detail="—")
            self._rows[key] = row
            layout.addWidget(row)

        layout.addStretch()
        self.refresh()

    def refresh(self):
        mapping = {
            "openai": "OpenAI API",
            "gemini": "Gemini API",
            "ollama": "Ollama",
            "mongodb": "MongoDB Memory",
            "voice": "Whisper",
            "gesture": "MediaPipe",
        }
        items = {i.name: i for i in self._registry.all()}
        for key, reg_name in mapping.items():
            item = items.get(reg_name)
            if item and key in self._rows:
                self._rows[key].update(item.connected, item.model)

        self._rows["model"].update(True, self._registry.primary_model_label())
        self._rows["memory"].update(True, "JSON Store Active")
        self._rows["health"].update(True, "100%")

    def set_health(self, pct: int):
        self._rows["health"].update(pct >= 80, f"{pct}%")

    def set_voice(self, online: bool, detail: str):
        self._rows["voice"].update(online, detail)

    def set_gesture(self, online: bool, detail: str):
        self._rows["gesture"].update(online, detail)

    def set_memory(self, detail: str):
        self._rows["memory"].update(True, detail)
