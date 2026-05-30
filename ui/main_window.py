"""
Main UI — Jarvis Desktop Voice Assistant
Ultra-premium design with frameless window, chat bubbles, acrylic-like dark theme,
and a Responsive Desktop System Controls side panel.
"""
import sys
import os
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QListWidget, QListWidgetItem,
    QSlider, QSpacerItem, QDialog, QTextEdit
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


class WorkflowDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Create Workflow")
        self.setFixedSize(420, 380)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {DARK_BG}; color: {TEXT_PRI}; }}
            QLabel {{ color: {TEXT_PRI}; font-size: 13px; }}
            QLineEdit, QTextEdit {{
                background-color: {CARD_BG};
                border: 1px solid {BORDER};
                border-radius: 12px;
                color: {TEXT_PRI};
                padding: 10px;
                font-size: 13px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
                color: white;
                border-radius: 14px;
                padding: 10px 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ opacity: 0.95; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Create a new workflow")
        title.setStyleSheet("font-size: 16px; font-weight: 800;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Workflow name"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Workflow steps (one action per line)"))
        self.definition_input = QTextEdit()
        self.definition_input.setFixedHeight(160)
        self.definition_input.setPlaceholderText("E.g. open chrome\nopen code\nset volume to 30%")
        layout.addWidget(self.definition_input)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #f87171;")
        layout.addWidget(self.message_label)

        button_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Workflow")
        self.save_btn.clicked.connect(self._on_save)
        button_row.addWidget(self.save_btn)
        layout.addLayout(button_row)

    def _on_save(self):
        name = self.name_input.text().strip()
        steps_raw = self.definition_input.toPlainText().strip()
        if not name:
            self.message_label.setText("Please enter a workflow name.")
            return
        if not steps_raw:
            self.message_label.setText("Please enter at least one workflow step.")
            return

        steps = [
            {"text": step.strip()} for step in steps_raw.splitlines() if step.strip()
        ]
        if not steps:
            self.message_label.setText("Please add valid workflow steps.")
            return

        self.controller.workflow_engine.create_workflow(name, steps, trigger=name)
        self.accept()


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
        self._refresh_workflow_list()
        self.workflow_editor_card.hide()
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

        self.btn_toggle_workflow = QPushButton("⚙")
        self.btn_toggle_workflow.setFixedSize(30, 30)
        self.btn_toggle_workflow.clicked.connect(self._toggle_workflow_editor)
        self.btn_toggle_workflow.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")
        title_layout.addWidget(self.btn_toggle_workflow)

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

        # Workflow Editor Panel (as floating window)
        self.workflow_editor_card = QFrame()
        self.workflow_editor_card.setWindowTitle("Workflow Editor")
        self.workflow_editor_card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {BORDER};
                border-radius: 0px;
            }}
            QLabel {{ color: {TEXT_PRI}; }}
            QLineEdit, QTextEdit {{
                background-color: {DARK_BG};
                border: 1px solid {BORDER};
                border-radius: 12px;
                color: {TEXT_PRI};
                padding: 10px;
                font-size: 13px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
                color: white;
                border-radius: 14px;
                padding: 10px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ opacity: 0.95; }}
        """)
        editor_layout = QVBoxLayout(self.workflow_editor_card)
        editor_layout.setContentsMargins(16, 16, 16, 16)
        editor_layout.setSpacing(12)

        editor_header = QLabel("Workflow Editor")
        editor_header.setStyleSheet("font-size: 15px; font-weight: 800;")
        editor_layout.addWidget(editor_header)

        # Saved Workflows List (compact)
        workflow_list_label = QLabel("Saved Workflows")
        workflow_list_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; font-weight: 700;")
        editor_layout.addWidget(workflow_list_label)

        self.workflow_list = QListWidget()
        self.workflow_list.setFixedHeight(90)
        self.workflow_list.setStyleSheet(f"""
            QListWidget {{ background-color: {DARK_BG}; border: 1px solid {BORDER}; border-radius: 12px; color: {TEXT_PRI}; }}
            QListWidget::item {{ padding: 6px; }}
            QListWidget::item:selected {{ background-color: {ACCENT}; color: white; }}
        """)
        self.workflow_list.itemSelectionChanged.connect(self._load_selected_workflow_into_editor)
        editor_layout.addWidget(self.workflow_list)

        # Form Fields Grid
        form_grid = QHBoxLayout()
        form_grid.setSpacing(12)

        name_col = QVBoxLayout()
        name_col.setSpacing(6)
        name_col.addWidget(QLabel("Name"))
        self.editor_name_input = QLineEdit()
        self.editor_name_input.setPlaceholderText("e.g. Morning routine")
        name_col.addWidget(self.editor_name_input)
        form_grid.addLayout(name_col)

        trigger_col = QVBoxLayout()
        trigger_col.setSpacing(6)
        trigger_col.addWidget(QLabel("Trigger phrase"))
        self.editor_trigger_input = QLineEdit()
        self.editor_trigger_input.setPlaceholderText("e.g. Start morning")
        trigger_col.addWidget(self.editor_trigger_input)
        form_grid.addLayout(trigger_col)

        editor_layout.addLayout(form_grid)

        # Steps Input
        steps_label = QLabel("Steps (one action per line)")
        steps_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; font-weight: 700;")
        editor_layout.addWidget(steps_label)

        self.editor_steps_input = QTextEdit()
        self.editor_steps_input.setFixedHeight(100)
        self.editor_steps_input.setPlaceholderText("open chrome\nopen code\nset volume to 30%")
        editor_layout.addWidget(self.editor_steps_input)

        # Status
        self.editor_status = QLabel("")
        self.editor_status.setStyleSheet("color: #fbbf24; font-size: 11px;")
        editor_layout.addWidget(self.editor_status)

        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.editor_save_btn = QPushButton("Save")
        self.editor_save_btn.clicked.connect(self._save_workflow_from_editor)
        button_row.addWidget(self.editor_save_btn)

        self.editor_run_btn = QPushButton("Run")
        self.editor_run_btn.clicked.connect(self._run_selected_workflow)
        button_row.addWidget(self.editor_run_btn)

        self.editor_delete_btn = QPushButton("Delete")
        self.editor_delete_btn.clicked.connect(self._delete_selected_workflow)
        button_row.addWidget(self.editor_delete_btn)

        self.editor_voice_btn = QPushButton("Voice Wizard")
        self.editor_voice_btn.clicked.connect(self._start_workflow_voice_wizard)
        button_row.addWidget(self.editor_voice_btn)

        editor_layout.addLayout(button_row)

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

        # Workflow editor section
        workflow_header = QLabel("WORKFLOW ACTIONS")
        workflow_header.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        side_layout.addWidget(workflow_header)

        self.btn_workflow_new = QPushButton("＋ New Workflow")
        self.btn_workflow_new.setStyleSheet(btn_style)
        self.btn_workflow_new.clicked.connect(self._open_workflow_dialog)
        side_layout.addWidget(self.btn_workflow_new)

        self.btn_workflow_run = QPushButton("▶ Run Workflow")
        self.btn_workflow_run.setStyleSheet(btn_style)
        self.btn_workflow_run.clicked.connect(self._run_selected_workflow)
        side_layout.addWidget(self.btn_workflow_run)

        self.btn_workflow_delete = QPushButton("🗑 Delete Workflow")
        self.btn_workflow_delete.setStyleSheet(btn_style)
        self.btn_workflow_delete.clicked.connect(self._delete_selected_workflow)
        side_layout.addWidget(self.btn_workflow_delete)

        self.btn_workflow_voice = QPushButton("🎙 Voice Workflow Wizard")
        self.btn_workflow_voice.setStyleSheet(btn_style)
        self.btn_workflow_voice.clicked.connect(self._start_workflow_voice_wizard)
        side_layout.addWidget(self.btn_workflow_voice)

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

    def _toggle_workflow_editor(self):
        if not hasattr(self, '_workflow_window_created'):
            # Convert workflow_editor_card to a standalone window
            self.workflow_editor_card.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.workflow_editor_card.setFixedSize(580, 560)
            self.workflow_editor_card.move(100, 100)
            self._workflow_window_created = True
        
        if self.workflow_editor_card.isVisible():
            self.workflow_editor_card.hide()
            self.btn_toggle_workflow.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SEC}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")
        else:
            self.workflow_editor_card.show()
            self.btn_toggle_workflow.setStyleSheet(f"QPushButton {{ background: transparent; color: {ACCENT}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: #ffffff11; }}")

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
            self._refresh_workflow_list()

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

    def _set_status_text(self, text: str, color: str = "#4ade80"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 800; letter-spacing: 2px;")

    def _open_workflow_dialog(self):
        dialog = WorkflowDialog(self.controller, self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_workflow_list()
            self._add_bubble("Workflow created! You can run it from the side panel or editor.", is_user=False)

    def _run_selected_workflow(self):
        item = self.workflow_list.currentItem()
        if not item:
            self._add_bubble("Please select a workflow to run.", is_user=False)
            return
        workflow_name = item.text().split(" — ")[0].strip()
        self.controller.process_text_input(f"run workflow {workflow_name}")
        self._refresh_workflow_list()

    def _delete_selected_workflow(self):
        item = self.workflow_list.currentItem()
        if not item:
            self._add_bubble("Please select a workflow to delete.", is_user=False)
            return
        workflow_name = item.text().split(" — ")[0].strip()
        removed = self.controller.workflow_engine.remove_workflow(workflow_name)
        if removed:
            self._refresh_workflow_list()
            self._add_bubble(f"Deleted workflow '{workflow_name}'.", is_user=False)
            self.editor_status.setText("")
        else:
            self._add_bubble(f"Could not delete workflow '{workflow_name}'.", is_user=False)

    def _load_selected_workflow_into_editor(self):
        item = self.workflow_list.currentItem()
        if not item:
            return
        workflow_name = item.text().split(" — ")[0].strip()
        workflow = self.controller.workflow_engine.get_workflow(workflow_name)
        if not workflow:
            return
        self.editor_name_input.setText(workflow.get("name", ""))
        self.editor_trigger_input.setText(workflow.get("trigger", ""))
        steps = workflow.get("steps", [])
        self.editor_steps_input.setPlainText("\n".join(step.get("text", "") for step in steps if step.get("text")))
        self.editor_status.setStyleSheet("color: #fbbf24; font-size: 12px;")
        self.editor_status.setText(f"Loaded workflow '{workflow_name}'. Edit or run it below.")

    def _save_workflow_from_editor(self):
        name = self.editor_name_input.text().strip()
        trigger = self.editor_trigger_input.text().strip()
        steps_raw = self.editor_steps_input.toPlainText().strip()
        if not name:
            self.editor_status.setStyleSheet("color: #f87171; font-size: 12px;")
            self.editor_status.setText("Please enter a workflow name.")
            return
        if not steps_raw:
            self.editor_status.setStyleSheet("color: #f87171; font-size: 12px;")
            self.editor_status.setText("Please enter at least one workflow step.")
            return

        steps = [{"text": step.strip()} for step in steps_raw.splitlines() if step.strip()]
        if not steps:
            self.editor_status.setStyleSheet("color: #f87171; font-size: 12px;")
            self.editor_status.setText("Please add valid workflow steps.")
            return

        self.controller.workflow_engine.create_workflow(name, steps, trigger=trigger or name)
        self._refresh_workflow_list()
        self.editor_status.setStyleSheet("color: #4ade80; font-size: 12px;")
        self.editor_status.setText(f"Workflow '{name}' saved.")

    def _start_workflow_voice_wizard(self):
        if getattr(self.controller, "is_listening", False):
            self._add_bubble("Please stop the main voice listener before using workflow voice wizard.", is_user=False)
            return

        self.btn_workflow_voice.setEnabled(False)
        QTimer.singleShot(0, lambda: self._set_status_text("LISTENING FOR WORKFLOW...", "#3b82f6"))
        thread = threading.Thread(target=self._listen_for_workflow_phrase, daemon=True)
        thread.start()

    def _listen_for_workflow_phrase(self):
        text = self.controller.stt.listen(timeout=10, phrase_time_limit=18)
        if text:
            QTimer.singleShot(0, lambda: self._add_bubble(f"Heard workflow: {text}", is_user=True))
            self.controller.process_text_input(text)
            QTimer.singleShot(0, self._refresh_workflow_list)
        else:
            QTimer.singleShot(0, lambda: self._add_bubble("Could not hear a workflow command. Try again.", is_user=False))
        QTimer.singleShot(0, lambda: self.btn_workflow_voice.setEnabled(True))
        QTimer.singleShot(0, lambda: self._on_status("idle"))

    def _refresh_workflow_list(self):
        if not hasattr(self, "workflow_list"):
            return
        self.workflow_list.clear()
        if not getattr(self.controller, "workflow_engine", None):
            return
        for workflow in self.controller.workflow_engine.list_workflows():
            trigger = workflow.get("trigger", "")
            title = workflow["name"]
            label = f"{title} — trigger: {trigger}" if trigger else title
            self.workflow_list.addItem(label)

    def closeEvent(self, event):
        self.controller.stop_listening()
        event.accept()
