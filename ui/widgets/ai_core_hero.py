"""Central AI Core hero — avatar centerpiece with state and waveform."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors
from ui.components.base import SectionHeader
from ui.components.waveform import WaveformWidget
from ui.avatar_widget import AvatarWidget
from ui.themes import glass_style


STATE_COLORS = {
    "idle": Colors.NEON_GREEN,
    "listening": Colors.NEON_BLUE,
    "thinking": Colors.NEON_YELLOW,
    "speaking": Colors.NEON_PURPLE,
}


class AiCoreHero(QFrame):
    """Large central AI core panel — primary visual focus."""

    def __init__(self):
        super().__init__()
        self.setObjectName("AiCoreHero")
        self.setStyleSheet(f"QFrame#AiCoreHero {{ {glass_style(20, True)} }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(300)

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(28)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(SectionHeader("AI Core"))
        self.state_badge = QLabel("IDLE")
        self.state_badge.setStyleSheet(f"""
            color: {Colors.NEON_GREEN};
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 3px;
        """)
        self.state_sub = QLabel("Awaiting wake word…")
        self.state_sub.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        self.waveform = WaveformWidget(bar_count=20)
        self.waveform.setFixedHeight(40)
        self.wake_label = QLabel("Wake: Hey Assistant")
        self.wake_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        left.addWidget(self.state_badge)
        left.addWidget(self.state_sub)
        left.addWidget(self.waveform)
        left.addWidget(self.wake_label)
        left.addStretch()
        root.addLayout(left, stretch=2)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)
        self.avatar = AvatarWidget()
        self.avatar.setFixedSize(240, 240)
        center.addWidget(self.avatar, alignment=Qt.AlignCenter)
        root.addLayout(center, stretch=3)

        right = QVBoxLayout()
        right.setSpacing(8)
        chips = [
            ("model_label", "Model", Colors.NEON_BLUE),
            ("memory_label", "Memory", Colors.NEON_CYAN),
            ("voice_label", "Voice", Colors.NEON_GREEN),
            ("gesture_label", "Gesture", Colors.NEON_PURPLE),
        ]
        self._chip_labels = {}
        for key, title, color in chips:
            chip = QFrame()
            chip.setStyleSheet(f"""
                QFrame {{
                    background: rgba(10, 20, 40, 0.5);
                    border-left: 3px solid {color};
                    border-radius: 10px;
                }}
            """)
            cl = QVBoxLayout(chip)
            cl.setContentsMargins(12, 8, 12, 8)
            cl.setSpacing(2)
            t = QLabel(title.upper())
            t.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700; letter-spacing: 1px;")
            v = QLabel("—")
            v.setWordWrap(True)
            v.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
            cl.addWidget(t)
            cl.addWidget(v)
            self._chip_labels[key] = v
            right.addWidget(chip)
        right.addStretch()
        root.addLayout(right, stretch=2)

    def set_state(self, state: str):
        self.avatar.set_state(state)
        color = STATE_COLORS.get(state, Colors.NEON_BLUE)
        self.state_badge.setText(state.upper())
        self.state_badge.setStyleSheet(f"""
            color: {color};
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 3px;
        """)
        hints = {
            "idle": "Awaiting wake word…",
            "listening": "Listening for your command…",
            "thinking": "Processing request…",
            "speaking": "Delivering response…",
        }
        self.state_sub.setText(hints.get(state, ""))
        self.waveform.set_active(state in ("listening", "speaking"))

    def set_wake_words(self, words: str):
        self.wake_label.setText(f"Wake: {words}")

    def set_model(self, label: str):
        self._chip_labels["model_label"].setText(label)

    def set_gesture_mode(self, enabled: bool):
        self._chip_labels["gesture_label"].setText("Enabled" if enabled else "Disabled")

    def set_voice_status(self, text: str):
        self._chip_labels["voice_label"].setText(text)

    def set_memory_status(self, text: str):
        self._chip_labels["memory_label"].setText(text)
