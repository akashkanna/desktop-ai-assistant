"""Collapsible left navigation sidebar."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea, QSizePolicy, QToolButton,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors, ThemeManager
from ui.themes import glass_style


NAV_ITEMS = [
    ("dashboard", "◉", "Dashboard"),
    ("voice", "🎙", "Voice Assistant"),
    ("gesture", "✋", "Gesture Control"),
    ("workflow", "⚡", "Workflow"),
    ("apps", "▦", "App Launcher"),
    ("system", "⚙", "System Control"),
    ("files", "📁", "Files & Folders"),
    ("screenshots", "📷", "Screenshots"),
    ("memory", "🧠", "AI Memory"),
    ("logs", "📋", "Logs"),
    ("settings", "🔧", "Settings"),
]


class CollapsibleSidebar(QFrame):
    page_selected = Signal(str)
    collapsed_changed = Signal(bool)

    EXPANDED_W = 240
    COLLAPSED_W = 64

    def __init__(self):
        super().__init__()
        self._collapsed = False
        self.setMinimumWidth(self.EXPANDED_W)
        self.setMaximumWidth(self.EXPANDED_W)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SIDEBAR};
                border-right: 1px solid {Colors.BORDER};
                border-top-left-radius: 18px;
                border-bottom-left-radius: 18px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 10)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(10, 8, 10, 8)
        self.brand = QLabel("JARVIS")
        self.brand.setStyleSheet(
            f"color: {Colors.NEON_BLUE}; font-size: 13px; font-weight: 900; letter-spacing: 3px;"
        )
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("☰")
        self.toggle_btn.setMinimumSize(32, 32)
        self.toggle_btn.setMaximumSize(40, 40)
        self.toggle_btn.setStyleSheet(f"""
            QToolButton {{
                background: rgba(10,20,40,0.6); border: 1px solid {Colors.BORDER};
                border-radius: 8px; color: {Colors.TEXT_SECONDARY}; font-size: 14px;
            }}
            QToolButton:hover {{ border-color: {Colors.NEON_BLUE}; color: {Colors.NEON_BLUE}; }}
        """)
        self.toggle_btn.clicked.connect(self.toggle_collapsed)
        top.addWidget(self.brand)
        top.addStretch()
        top.addWidget(self.toggle_btn)
        layout.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        nav_host = QWidget()
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)
        self._buttons: dict[str, QPushButton] = {}
        for key, icon, label in NAV_ITEMS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setProperty("full_label", f"{icon}  {label}")
            btn.setProperty("icon_only", icon)
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(label)
            btn.clicked.connect(lambda checked=False, k=key: self._select(k))
            self._buttons[key] = btn
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        scroll.setWidget(nav_host)
        layout.addWidget(scroll, stretch=1)

        self.status_lbl = QLabel("● Online")
        self.status_lbl.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 10px; font-weight: 700; padding: 8px 14px;"
        )
        layout.addWidget(self.status_lbl)
        self._apply_styles()
        self._select("dashboard")

    def toggle_collapsed(self):
        self._collapsed = not self._collapsed
        target = self.COLLAPSED_W if self._collapsed else self.EXPANDED_W
        self.brand.setVisible(not self._collapsed)
        for btn in self._buttons.values():
            text = btn.property("icon_only") if self._collapsed else btn.property("full_label")
            btn.setText(text)
        self.status_lbl.setVisible(not self._collapsed)
        self.setMinimumWidth(target)
        self.setMaximumWidth(target)
        self._apply_styles()
        self.updateGeometry()
        self.repaint()
        parent = self.parentWidget()
        if parent and parent.layout():
            parent.layout().invalidate()
            parent.updateGeometry()
            parent.update()
        self.collapsed_changed.emit(self._collapsed)

    def _apply_styles(self):
        align = "center" if self._collapsed else "left"
        for btn in self._buttons.values():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {Colors.TEXT_SECONDARY};
                    border: none; border-left: 3px solid transparent;
                    border-radius: 0 14px 14px 0; text-align: {align};
                    padding: 10px 12px; font-size: 12px; font-weight: 600;
                }}
                QPushButton:hover {{ background: #00A3FF11; color: {Colors.TEXT_PRIMARY}; }}
            """)

    def _select(self, key: str):
        for k, btn in self._buttons.items():
            active = k == key
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00A3FF33,stop:1 #7B61FF22);
                        color: {Colors.TEXT_PRIMARY}; border: none;
                        border-left: 3px solid {Colors.NEON_BLUE};
                        border-radius: 0 14px 14px 0; text-align: left;
                        padding: 10px 12px; font-size: 12px; font-weight: 700;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; color: {Colors.TEXT_SECONDARY};
                        border: none; border-left: 3px solid transparent;
                        border-radius: 0 14px 14px 0; text-align: left;
                        padding: 10px 12px; font-size: 12px; font-weight: 600;
                    }}
                    QPushButton:hover {{ background: #00A3FF11; color: {Colors.TEXT_PRIMARY}; }}
                """)
        self.page_selected.emit(key)

    def set_assistant_status(self, online: bool, label: str = ""):
        text = label or ("Online" if online else "Offline")
        color = Colors.SUCCESS if online else Colors.DANGER
        self.status_lbl.setText(f"● {text}")
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; padding: 8px 14px;"
        )
