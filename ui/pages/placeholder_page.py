"""Secondary pages for sidebar navigation."""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.base import PageShell, GlassCard, SectionHeader
from services.integration_hooks import IntegrationRegistry


PAGE_META = {
    "voice": ("Voice Assistant", "Control speech recognition, wake words, and TTS output."),
    "gesture": ("Gesture Control", "MediaPipe hand tracking for cursor and window gestures."),
    "workflow": ("Workflow Automation", "Create, schedule, and execute multi-step automations."),
    "apps": ("App & Window Manager", "Launch applications and manage desktop windows."),
    "system": ("System Controls", "Volume, power, lock, sleep, and system-level actions."),
    "files": ("Files & Folders", "Browse and manage files with voice commands."),
    "screenshots": ("Screenshots", "Capture and manage desktop screenshots."),
    "memory": ("AI Memory", "View stored preferences, contacts, and session history."),
    "logs": ("Logs", "Full assistant activity and debug logs."),
    "settings": ("Settings", "Configure assistant behavior, APIs, and UI preferences."),
    "help": ("Help", "Command reference and quick start guide."),
}


class PlaceholderPage(QScrollArea):
    def __init__(self, page_key: str):
        super().__init__()
        self.page_key = page_key
        self.setWidgetResizable(True)
        self.setStyleSheet("background: transparent; border: none;")

        title, desc = PAGE_META.get(page_key, (page_key.title(), ""))
        shell = PageShell()
        shell.layout_ref.addWidget(SectionHeader(title))

        intro = QLabel(desc)
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 14px;")
        shell.layout_ref.addWidget(intro)

        card = GlassCard(radius=16, glow=True)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        hint = QLabel(
            "This module is wired to the Jarvis backend. "
            "Use the Dashboard for full control, or send voice/text commands."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px;")
        cl.addWidget(hint)

        if page_key == "settings":
            registry = IntegrationRegistry()
            for item in registry.all():
                row = QFrame()
                row.setStyleSheet(f"background: {Colors.BG_INPUT}; border-radius: 10px; padding: 4px;")
                rl = QVBoxLayout(row)
                name = QLabel(item.name)
                name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: 700;")
                status = QLabel(f"{'Connected' if item.connected else 'Not configured'} — {item.model}")
                status.setStyleSheet(
                    f"color: {Colors.SUCCESS if item.connected else Colors.TEXT_MUTED}; font-size: 11px;"
                )
                rl.addWidget(name)
                rl.addWidget(status)
                cl.addWidget(row)

        shell.layout_ref.addWidget(card)
        shell.layout_ref.addStretch()
        self.setWidget(shell)
        self._shell = shell

    def add_widget(self, widget):
        """Insert an extra panel below the intro text."""
        self._shell.layout_ref.insertWidget(2, widget)


class VoiceAssistantPage(PlaceholderPage):
    def __init__(self):
        super().__init__("voice")


class ChatLogPanel(GlassCard):
    """Compact chat transcript used on voice page."""

    def __init__(self):
        super().__init__(radius=16)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.addWidget(SectionHeader("Conversation"))
        self._messages = QVBoxLayout()
        self._layout.addLayout(self._messages)

    def add_message(self, text: str, is_user: bool):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        bg = Colors.BG_CARD_HOVER if is_user else Colors.BG_INPUT
        align = "right" if is_user else "left"
        border_color = Colors.NEON_BLUE if is_user else Colors.NEON_PURPLE
        lbl.setStyleSheet(f"""
            background: {bg};
            border-left: 3px solid {border_color};
            border-radius: 10px;
            padding: 10px 14px;
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
        """)
        lbl.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)
        self._messages.addWidget(lbl)
