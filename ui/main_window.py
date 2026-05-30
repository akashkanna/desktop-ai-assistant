"""
Main UI — Jarvis Desktop Voice Assistant
Ultra-premium design with frameless window, chat bubbles, acrylic-like dark theme,
and a Responsive Desktop System Controls side panel.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QListWidget, QListWidgetItem,
    QSlider, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, Slot, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QMouseEvent

from core.assistant_controller import AssistantController
from ui.avatar_widget import AvatarWidget
import automation.system_controls as sys_ctrl

# ─────────────────────────────── helpers ───────────────────────────────

def shadow(widget, radius=24, color="#000000", offset=(0, 4)):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    eff.setColor(QColor(color))
    eff.setOffset(*offset)
    widget.setGraphicsEffect(eff)
    return eff


# ── Colors ──
DARK_BG   = "#0b0c10"
CARD_BG   = "#15161e"
SIDE_BG   = "#101117"
BUBBLE_U  = "#2a2b38"
BUBBLE_J  = "#1f1d36"
BORDER    = "#262736"
ACCENT    = "#3b82f6"
ACCENT2   = "#8b5cf6"
TEXT_PRI  = "#f8fafc"
TEXT_SEC  = "#94a3b8"


class FramelessWindow(QMainWindow):
    """Base class for a frameless window with custom dragging."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


class ChatBubble(QWidget):
    """A custom widget for rendering chat messages like iMessage."""
    def __init__(self, text: str, is_user: bool = True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Style the bubble
        if is_user:
            bubble.setStyleSheet(f"""
                background-color: {BUBBLE_U};
                color: {TEXT_PRI};
                border-radius: 16px;
                border-top-right-radius: 4px;
                padding: 12px 18px;
                font-size: 14px;
                line-height: 1.4;
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet(f"""
                background-color: {BUBBLE_J};
                color: {TEXT_PRI};
                border: 1px solid #2d2a4a;
                border-radius: 16px;
                border-top-left-radius: 4px;
                padding: 12px 18px;
                font-size: 14px;
                line-height: 1.4;
            """)
            layout.addWidget(bubble)
            layout.addStretch()


class MainWindow(FramelessWindow):
    sig_status      = Signal(str)
    sig_user_text   = Signal(str)
    sig_jarvis_text = Signal(str)
    sig_mute        = Signal(bool)
    sig_avatar      = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis — AI Desktop Assistant")
        # Start at a wide layout to show the side panel
        self.resize(850, 800)
        self.setMinimumSize(400, 600)

        self._side_panel_visible = True
        self._user_toggled_side = False

        # Connect signals
        self.sig_status.connect(self._on_status)
        self.sig_user_text.connect(self._on_user_text)
        self.sig_jarvis_text.connect(self._on_jarvis_text)
        self.sig_mute.connect(self._on_mute)
        self.sig_avatar.connect(self._on_avatar_state)

        self._build_ui()
        
        # Init system controls
        self._init_system_controls()

        self.controller = AssistantController(ui_callback=self._controller_cb)
        QTimer.singleShot(800, self._auto_start)

    def _build_ui(self):
        # ── Main Background Container ──
        self.bg = QFrame(self)
        self.bg.setObjectName("bg")
        self.bg.setStyleSheet(f"""
            #bg {{
                background-color: {DARK_BG};
                border: 1px solid {BORDER};
                border-radius: 20px;
            }}
            QWidget {{
                font-family: 'Segoe UI', 'Inter', sans-serif;
                color: {TEXT_PRI};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self.setCentralWidget(self.bg)
        
        self.main_h_layout = QHBoxLayout(self.bg)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # ── Main Content Container ──
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title Bar
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)
        
        self.btn_toggle_side = QPushButton("≡")
        self.btn_toggle_side.setFixedSize(30, 30)
        self.btn_toggle_side.clicked.connect(self._toggle_side_panel_manual)
        self.btn_toggle_side.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-size: 18px; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")
        title_layout.addWidget(self.btn_toggle_side)

        title_lbl = QLabel("  JARVIS")
        title_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; font-weight: 800; letter-spacing: 4px;")
        title_layout.addWidget(title_lbl)
        
        title_layout.addStretch()

        btn_min = QPushButton("─")
        btn_min.setFixedSize(30, 30)
        btn_min.clicked.connect(self.showMinimized)
        btn_min.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")
        
        self.btn_max = QPushButton("☐")
        self.btn_max.setFixedSize(30, 30)
        self.btn_max.clicked.connect(self._toggle_maximize)
        self.btn_max.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ff4444; color: white; }}")
        
        title_layout.addWidget(btn_min)
        title_layout.addWidget(self.btn_max)
        title_layout.addWidget(btn_close)
        main_layout.addWidget(title_bar)

        # Avatar Section
        avatar_container = QWidget()
        av_layout = QVBoxLayout(avatar_container)
        av_layout.setContentsMargins(0, 10, 0, 20)
        av_layout.setAlignment(Qt.AlignCenter)

        self.avatar = AvatarWidget()
        av_layout.addWidget(self.avatar, alignment=Qt.AlignCenter)

        self.status_label = QLabel("IDLE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: #4ade80; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        av_layout.addWidget(self.status_label)
        
        main_layout.addWidget(avatar_container)

        # Chat Area
        self.chat_list = QListWidget()
        self.chat_list.setSelectionMode(QListWidget.NoSelection)
        self.chat_list.setStyleSheet(f"QListWidget {{ background: transparent; border: none; outline: none; }}")
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        main_layout.addWidget(self.chat_list, stretch=1)

        # Input Area
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(24, 16, 24, 24)
        input_layout.setSpacing(16)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)

        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.clicked.connect(self._toggle_listen)
        self._style_btn(self.listen_btn, primary=True)
        shadow(self.listen_btn, 20, ACCENT, (0, 4))
        ctrl_row.addWidget(self.listen_btn, stretch=1)

        self.mute_btn = QPushButton("Voice On")
        self.mute_btn.clicked.connect(self._toggle_mute)
        self._style_btn(self.mute_btn, primary=False)
        ctrl_row.addWidget(self.mute_btn)
        
        input_layout.addLayout(ctrl_row)

        text_row = QHBoxLayout()
        text_row.setSpacing(10)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Message Jarvis...")
        self.text_input.returnPressed.connect(self._send_text)
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {CARD_BG};
                border: 1px solid {BORDER};
                border-radius: 22px;
                padding: 12px 20px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        text_row.addWidget(self.text_input, stretch=1)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(44, 44)
        self.send_btn.clicked.connect(self._send_text)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {ACCENT}, stop:1 {ACCENT2});
                border-radius: 22px;
                font-size: 16px;
                color: white;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        shadow(self.send_btn, 16, ACCENT, (0, 3))
        text_row.addWidget(self.send_btn)

        input_layout.addLayout(text_row)
        main_layout.addWidget(input_container)

        self.main_h_layout.addWidget(self.main_content, stretch=1)

        # ── Side Panel (System Controls) ──
        self.side_panel = QFrame()
        self.side_panel.setFixedWidth(280)
        self.side_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {SIDE_BG};
                border-left: 1px solid {BORDER};
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
            }}
        """)
        side_layout = QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(24)

        # Header
        side_header = QLabel("SYSTEM CONTROLS")
        side_header.setStyleSheet(f"color: {ACCENT2}; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        side_layout.addWidget(side_header)

        # Volume Section
        vol_container = QWidget()
        vol_layout = QVBoxLayout(vol_container)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(8)
        
        self.vol_label = QLabel("Volume: 50%")
        self.vol_label.setStyleSheet(f"color: {TEXT_PRI}; font-size: 13px; font-weight: 600;")
        vol_layout.addWidget(self.vol_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border-radius: 4px;
                height: 8px;
                background: {BORDER};
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                border: 2px solid {ACCENT2};
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
        """)
        self.vol_slider.valueChanged.connect(self._on_vol_changed)
        vol_layout.addWidget(self.vol_slider)
        side_layout.addWidget(vol_container)

        # Action Buttons
        actions_header = QLabel("ACTIONS")
        actions_header.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        side_layout.addWidget(actions_header)

        btn_style = f"""
            QPushButton {{
                background-color: {CARD_BG};
                color: {TEXT_PRI};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 12px;
                font-weight: 600;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #202230;
                border: 1px solid {ACCENT};
            }}
        """

        self.btn_min_all = QPushButton("🗕 Minimize All")
        self.btn_min_all.setStyleSheet(btn_style)
        self.btn_min_all.clicked.connect(lambda: sys_ctrl.minimize_all_windows())
        side_layout.addWidget(self.btn_min_all)

        self.btn_sleep = QPushButton("🌙 Sleep Mode")
        self.btn_sleep.setStyleSheet(btn_style)
        self.btn_sleep.clicked.connect(lambda: sys_ctrl.sleep_system())
        side_layout.addWidget(self.btn_sleep)

        self.btn_lock = QPushButton("🔒 Lock Screen")
        self.btn_lock.setStyleSheet(btn_style)
        self.btn_lock.clicked.connect(lambda: sys_ctrl.lock_screen())
        side_layout.addWidget(self.btn_lock)

        self.btn_restart = QPushButton("🔄 Restart PC")
        self.btn_restart.setStyleSheet(btn_style)
        self.btn_restart.clicked.connect(lambda: sys_ctrl.restart_system())
        side_layout.addWidget(self.btn_restart)

        self.btn_shutdown = QPushButton("⏻ Shutdown PC")
        self.btn_shutdown.setStyleSheet(btn_style.replace(ACCENT, "#ef4444"))
        self.btn_shutdown.clicked.connect(lambda: sys_ctrl.shutdown_system())
        side_layout.addWidget(self.btn_shutdown)

        side_layout.addStretch()
        self.main_h_layout.addWidget(self.side_panel)

    def resizeEvent(self, event):
        """Responsive behavior: hide side panel if window gets too small, unless manually toggled."""
        super().resizeEvent(event)
        if not self._user_toggled_side:
            if self.width() < 750 and self.side_panel.isVisible():
                self.side_panel.hide()
                self._side_panel_visible = False
            elif self.width() >= 750 and not self.side_panel.isVisible():
                self.side_panel.show()
                self._side_panel_visible = True

    def _toggle_side_panel_manual(self):
        self._user_toggled_side = True
        self._side_panel_visible = not self._side_panel_visible
        self.side_panel.setVisible(self._side_panel_visible)

    def _init_system_controls(self):
        vol = sys_ctrl.get_volume()
        if vol >= 0:
            self.vol_slider.setValue(vol)
            self.vol_label.setText(f"Volume: {vol}%")

    def _on_vol_changed(self, val):
        self.vol_label.setText(f"Volume: {val}%")
        sys_ctrl.set_volume(val)

    def _style_btn(self, btn, primary=True, active=False):
        if primary:
            if active:
                bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ef4444, stop:1 #d946ef)"
                shadow_col = "#ef4444"
            else:
                bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2})"
                shadow_col = ACCENT
            btn.setStyleSheet(f"""
                QPushButton {{ background: {bg}; border-radius: 20px; padding: 12px; font-weight: 700; font-size: 13px; color: white; }}
                QPushButton:hover {{ opacity: 0.9; }}
            """)
            shadow(btn, 20, shadow_col, (0, 4))
        else:
            if active:
                btn.setStyleSheet(f"QPushButton {{ background: #450a0a; border: 1px solid #7f1d1d; border-radius: 20px; padding: 12px 20px; font-weight: 700; color: #f87171; }}")
            else:
                btn.setStyleSheet(f"QPushButton {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 20px; padding: 12px 20px; font-weight: 700; color: {TEXT_SEC}; }}")

    def _auto_start(self):
        self._add_bubble("Hello! I am Jarvis. How can I help you today?", is_user=False)
        self.controller.start_listening()

    def _add_bubble(self, text: str, is_user: bool):
        bubble = ChatBubble(text, is_user)
        item = QListWidgetItem()
        item.setSizeHint(bubble.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, bubble)
        self.chat_list.scrollToBottom()

    def _controller_cb(self, status=None, user_text=None, assistant_text=None, is_muted=None, avatar_state=None):
        if status is not None: self.sig_status.emit(status)
        if user_text is not None: self.sig_user_text.emit(user_text)
        if assistant_text is not None: self.sig_jarvis_text.emit(assistant_text)
        if is_muted is not None: self.sig_mute.emit(is_muted)
        if avatar_state is not None: self.sig_avatar.emit(avatar_state)

    @Slot(str)
    def _on_status(self, status: str):
        st = status.lower()
        if "listen" in st:
            self.status_label.setText("LISTENING")
            self.status_label.setStyleSheet("color: #3b82f6; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.listen_btn.setText("Stop Listening")
            self._style_btn(self.listen_btn, primary=True, active=True)
        elif "think" in st or "execut" in st:
            self.status_label.setText("THINKING")
            self.status_label.setStyleSheet("color: #eab308; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        elif "speak" in st:
            self.status_label.setText("SPEAKING")
            self.status_label.setStyleSheet("color: #a855f7; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
        else:
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("color: #4ade80; font-size: 12px; font-weight: 800; letter-spacing: 2px;")
            self.listen_btn.setText("Start Listening")
            self._style_btn(self.listen_btn, primary=True, active=False)

    @Slot(str)
    def _on_user_text(self, text: str):
        self._add_bubble(text, is_user=True)

    @Slot(str)
    def _on_jarvis_text(self, text: str):
        self._add_bubble(text, is_user=False)

    @Slot(bool)
    def _on_mute(self, is_muted: bool):
        self.mute_btn.setText("Voice Off" if is_muted else "Voice On")
        self._style_btn(self.mute_btn, primary=False, active=is_muted)

    @Slot(str)
    def _on_avatar_state(self, state: str):
        self.avatar.set_state(state)

    def _send_text(self):
        text = self.text_input.text().strip()
        if text:
            self.text_input.clear()
            self.controller.process_text_input(text)

    def _toggle_listen(self):
        if self.controller.is_listening: self.controller.stop_listening()
        else: self.controller.start_listening()

    def _toggle_mute(self):
        self.controller.toggle_mute()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("☐")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")

    def closeEvent(self, event):
        self.controller.stop_listening()
        event.accept()
