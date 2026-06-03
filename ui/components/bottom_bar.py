"""Bottom AI control bar — adapts to available width."""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy, QWidget,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.waveform import WaveformWidget
from ui.layout.responsive import Breakpoints


class MicButton(QPushButton):
    def __init__(self):
        super().__init__("🎤")
        self.setFixedSize(48, 48)
        self.setCursor(Qt.PointingHandCursor)
        self._listening = False
        self._apply_style()

    def set_listening(self, listening: bool):
        self._listening = listening
        self._apply_style()

    def _apply_style(self):
        if self._listening:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                        stop:0 {Colors.NEON_BLUE}, stop:1 {Colors.NEON_PURPLE});
                    border: 2px solid {Colors.NEON_BLUE};
                    border-radius: 24px;
                    font-size: 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_CARD};
                    border: 2px solid {Colors.NEON_BLUE};
                    border-radius: 24px;
                    font-size: 18px;
                }}
                QPushButton:hover {{ background-color: #00A3FF22; }}
            """)


class BottomControlBar(QFrame):
    listen_toggled = Signal()
    mute_toggled = Signal()
    gesture_toggled = Signal()
    voice_mode_toggled = Signal()
    emergency_stop = Signal()
    chat_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border-top: 1px solid {Colors.BORDER};
                border-bottom-right-radius: 18px;
            }}
        """)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(14, 10, 14, 10)
        self._root.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.mic_btn = MicButton()
        self.mic_btn.clicked.connect(self.listen_toggled.emit)
        row1.addWidget(self.mic_btn, alignment=Qt.AlignTop)

        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(6)
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumHeight(18)
        self.status_label.setStyleSheet(
            f"color: {Colors.NEON_BLUE}; font-size: 12px; font-weight: 800;"
        )
        self.waveform = WaveformWidget(bar_count=28)
        self.waveform.setFixedHeight(22)
        self.waveform.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_col.addWidget(self.status_label)
        status_col.addWidget(self.waveform)

        self._status_host = QWidget()
        self._status_host.setLayout(status_col)
        self._status_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row1.addWidget(self._status_host, stretch=1)

        chat_row = QHBoxLayout()
        chat_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a command…")
        self.chat_input.setMinimumHeight(36)
        self.chat_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.chat_input.returnPressed.connect(self._submit_chat)
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setStyleSheet(ThemeManager.gradient_button())
        self.send_btn.clicked.connect(self._submit_chat)
        chat_row.addWidget(self.chat_input, stretch=1)
        chat_row.addWidget(self.send_btn)
        row1.addLayout(chat_row, stretch=2)

        self._root.addLayout(row1)

        toggles = QHBoxLayout()
        toggles.setSpacing(8)
        self.gesture_btn = QPushButton("✋ Gesture: Off")
        self.voice_btn = QPushButton("🔊 Voice: On")
        self.stop_btn = QPushButton("⛔ STOP")
        for btn in (self.gesture_btn, self.voice_btn, self.stop_btn):
            btn.setMinimumHeight(32)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gesture_btn.setStyleSheet(ThemeManager.ghost_button())
        self.voice_btn.setStyleSheet(ThemeManager.ghost_button())
        self.stop_btn.setStyleSheet(ThemeManager.gradient_button(danger=True))
        self.gesture_btn.clicked.connect(self.gesture_toggled.emit)
        self.voice_btn.clicked.connect(self.voice_mode_toggled.emit)
        self.stop_btn.clicked.connect(self.emergency_stop.emit)
        toggles.addWidget(self.gesture_btn)
        toggles.addWidget(self.voice_btn)
        toggles.addWidget(self.stop_btn)
        self._root.addLayout(toggles)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < Breakpoints.COMPACT
        self._status_host.setVisible(not compact)
        gest_on = "On" in self.gesture_btn.text()
        muted = "Off" in self.voice_btn.text() and "Voice" in self.voice_btn.text()
        if compact:
            self.gesture_btn.setText(f"✋ {'On' if gest_on else 'Off'}")
            self.voice_btn.setText("🔇" if muted else "🔊")
        else:
            self.gesture_btn.setText(f"✋ Gesture: {'On' if gest_on else 'Off'}")
            self.voice_btn.setText("🔇 Voice: Off" if muted else "🔊 Voice: On")

    def _submit_chat(self):
        text = self.chat_input.text().strip()
        if text:
            self.chat_input.clear()
            self.chat_submitted.emit(text)

    def set_listening(self, listening: bool):
        self.mic_btn.set_listening(listening)
        self.status_label.setText("Listening…" if listening else "Ready")
        self.waveform.set_active(listening)

    def set_status(self, text: str):
        self.status_label.setText(text)
        active = any(w in text.lower() for w in ("listen", "speak", "think"))
        self.waveform.set_active(active)

    def set_gesture_enabled(self, enabled: bool):
        compact = self.width() < Breakpoints.COMPACT
        if compact:
            self.gesture_btn.setText(f"✋ {'On' if enabled else 'Off'}")
        else:
            self.gesture_btn.setText(f"✋ Gesture: {'On' if enabled else 'Off'}")

    def set_voice_muted(self, muted: bool):
        compact = self.width() < Breakpoints.COMPACT
        if compact:
            self.voice_btn.setText("🔇" if muted else "🔊")
        else:
            self.voice_btn.setText("🔇 Voice: Off" if muted else "🔊 Voice: On")
