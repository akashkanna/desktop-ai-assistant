"""Premium bottom command dock."""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.waveform import WaveformWidget
from ui.themes import glass_style


class CommandDock(QFrame):
    listen_toggled = Signal()
    mute_toggled = Signal()
    gesture_toggled = Signal()
    camera_toggled = Signal()
    emergency_stop = Signal()
    chat_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("CommandDock")
        self.setMinimumHeight(88)
        self.setStyleSheet(f"""
            QFrame#CommandDock {{
                {glass_style(0)}
                background-color: rgba(8, 16, 32, 0.92);
                border-top: 1px solid {Colors.BORDER};
                border-bottom-right-radius: 18px;
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(52, 52)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.clicked.connect(self.listen_toggled.emit)
        self._listening = False
        self._style_mic()
        row1.addWidget(self.mic_btn)

        wave_col = QVBoxLayout()
        wave_col.setSpacing(4)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            f"color: {Colors.NEON_BLUE}; font-size: 12px; font-weight: 800;"
        )
        self.waveform = WaveformWidget(bar_count=36)
        self.waveform.setFixedHeight(24)
        wave_col.addWidget(self.status_label)
        wave_col.addWidget(self.waveform)
        row1.addLayout(wave_col, stretch=1)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Enter command or message…")
        self.chat_input.setMinimumHeight(40)
        self.chat_input.returnPressed.connect(self._submit)
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet(ThemeManager.gradient_button())
        self.send_btn.clicked.connect(self._submit)
        row1.addWidget(self.chat_input, stretch=2)
        row1.addWidget(self.send_btn)
        root.addLayout(row1)

        toggles = QHBoxLayout()
        toggles.setSpacing(8)
        self.voice_btn = QPushButton("🔊 Voice: On")
        self.gesture_btn = QPushButton("✋ Gesture: Off")
        self.camera_btn = QPushButton("📷 Camera: Off")
        self.stop_btn = QPushButton("⛔ EMERGENCY STOP")
        for btn in (self.voice_btn, self.gesture_btn, self.camera_btn):
            btn.setStyleSheet(ThemeManager.ghost_button())
            btn.setMinimumHeight(32)
            toggles.addWidget(btn)
        self.stop_btn.setStyleSheet(ThemeManager.gradient_button(danger=True))
        self.stop_btn.setMinimumHeight(32)
        toggles.addWidget(self.stop_btn, stretch=1)
        self.voice_btn.clicked.connect(self.mute_toggled.emit)
        self.gesture_btn.clicked.connect(self.gesture_toggled.emit)
        self.camera_btn.clicked.connect(self.camera_toggled.emit)
        self.stop_btn.clicked.connect(self.emergency_stop.emit)
        root.addLayout(toggles)

    def _style_mic(self):
        if self._listening:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qradialgradient(cx:0.5,cy:0.5,radius:0.8,stop:0 {Colors.NEON_BLUE},stop:1 {Colors.NEON_PURPLE});
                    border: 2px solid {Colors.NEON_BLUE}; border-radius: 26px; font-size: 20px;
                }}
            """)
        else:
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(10,20,40,0.8); border: 2px solid {Colors.NEON_BLUE};
                    border-radius: 26px; font-size: 20px;
                }}
                QPushButton:hover {{ background: #00A3FF22; }}
            """)

    def _submit(self):
        text = self.chat_input.text().strip()
        if text:
            self.chat_input.clear()
            self.chat_submitted.emit(text)

    def set_listening(self, listening: bool):
        self._listening = listening
        self._style_mic()
        self.status_label.setText("Listening…" if listening else "Ready")
        self.waveform.set_active(listening)

    def set_status(self, text: str):
        self.status_label.setText(text)
        self.waveform.set_active(any(w in text.lower() for w in ("listen", "speak", "think")))

    def set_gesture_enabled(self, enabled: bool):
        self.gesture_btn.setText(f"✋ Gesture: {'On' if enabled else 'Off'}")

    def set_voice_muted(self, muted: bool):
        self.voice_btn.setText(f"🔇 Voice: Off" if muted else f"🔊 Voice: On")

    def set_camera_enabled(self, enabled: bool):
        self.camera_btn.setText(f"📷 Camera: {'On' if enabled else 'Off'}")
