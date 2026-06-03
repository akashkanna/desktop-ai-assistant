"""Hero panel with avatar, status, and wake word info."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt

from ui.theme.theme_manager import Colors
from ui.components.base import GlassCard, SectionHeader
from ui.components.waveform import WaveformWidget
from ui.avatar_widget import AvatarWidget
from ui.layout.responsive import ResponsiveHeroLayout


class HeroPanel(GlassCard):
    def __init__(self):
        super().__init__(radius=18, glow=True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        self._responsive = ResponsiveHeroLayout()
        outer.addWidget(self._responsive)

        self._left = QWidget()
        left = QVBoxLayout(self._left)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(6)
        self.status_title = QLabel("STATUS: IDLE")
        self.status_title.setWordWrap(True)
        self.status_title.setStyleSheet(f"""
            color: {Colors.NEON_BLUE};
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 1px;
        """)
        self.left_wave = WaveformWidget(bar_count=16)
        self.left_wave.setMinimumHeight(28)
        self.left_wave.setMaximumHeight(36)
        self.status_hint = QLabel("Say 'Hey Assistant' or 'Jarvis'")
        self.status_hint.setWordWrap(True)
        self.status_hint.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        left.addWidget(self.status_title)
        left.addWidget(self.left_wave)
        left.addWidget(self.status_hint)

        self._center = QWidget()
        center = QVBoxLayout(self._center)
        center.setContentsMargins(0, 0, 0, 0)
        center.setAlignment(Qt.AlignCenter)
        self.avatar = AvatarWidget()
        self.avatar.setFixedSize(140, 140)
        center.addWidget(self.avatar, alignment=Qt.AlignCenter)

        self._right = QWidget()
        right = QVBoxLayout(self._right)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        right.addWidget(SectionHeader("Assistant Config"))
        self.wake_label = QLabel("WAKE WORD: Hey Assistant")
        self.wake_label.setWordWrap(True)
        self.wake_label.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 12px; font-weight: 700;"
        )
        self.mode_label = QLabel("MODE: Voice + Gesture")
        self.mode_label.setWordWrap(True)
        self.mode_label.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"
        )
        self.model_label = QLabel("MODEL: Offline Intent Parser")
        self.model_label.setWordWrap(True)
        self.model_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        right.addWidget(self.wake_label)
        right.addWidget(self.mode_label)
        right.addWidget(self.model_label)
        right.addStretch()

        self._responsive.set_sections(self._left, self._center, self._right)

    def set_state(self, state: str):
        self.avatar.set_state(state)
        state_upper = state.upper()
        colors = {
            "idle": Colors.NEON_GREEN,
            "listening": Colors.NEON_BLUE,
            "thinking": Colors.NEON_YELLOW,
            "speaking": Colors.NEON_PURPLE,
        }
        color = colors.get(state, Colors.NEON_BLUE)
        self.status_title.setText(f"STATUS: {state_upper}")
        self.status_title.setStyleSheet(f"""
            color: {color};
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 1px;
        """)
        self.left_wave.set_active(state in ("listening", "speaking"))

    def set_model(self, label: str):
        self.model_label.setText(f"MODEL: {label}")

    def set_gesture_mode(self, enabled: bool):
        mode = "Voice + Gesture" if enabled else "Voice Only"
        self.mode_label.setText(f"MODE: {mode}")

    def set_wake_words(self, words: str):
        self.wake_label.setText(f"WAKE WORD: {words}")
