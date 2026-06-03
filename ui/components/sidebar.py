"""Left navigation sidebar with scrollable nav and pinned status."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QWidget,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.base import GlassCard


NAV_ITEMS = [
    ("dashboard", "◉", "Dashboard"),
    ("voice", "🎙", "Voice Assistant"),
    ("gesture", "✋", "Gesture Control"),
    ("workflow", "⚡", "Workflow"),
    ("apps", "▦", "App & Windows"),
    ("system", "⚙", "System Controls"),
    ("files", "📁", "Files & Folders"),
    ("screenshots", "📷", "Screenshots"),
    ("memory", "🧠", "AI Memory"),
    ("logs", "📋", "Logs"),
    ("settings", "🔧", "Settings"),
    ("help", "❔", "Help"),
]


class SidebarLogo(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(68)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        ring = QLabel("J")
        ring.setFixedSize(44, 44)
        ring.setAlignment(Qt.AlignCenter)
        ring.setStyleSheet(f"""
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                stop:0 {Colors.BG_CARD_HOVER}, stop:1 {Colors.BG_PRIMARY});
            border: 2px solid {Colors.NEON_BLUE};
            border-radius: 22px;
            color: {Colors.NEON_BLUE};
            font-size: 18px;
            font-weight: 900;
        """)
        layout.addWidget(ring, alignment=Qt.AlignCenter)

        subtitle = QLabel("JARVIS OS")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 8px; letter-spacing: 2px; font-weight: 700;"
        )
        layout.addWidget(subtitle)


class NavButton(QPushButton):
    def __init__(self, key: str, icon: str, label: str):
        super().__init__(f" {icon}  {label}")
        self.page_key = key
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._apply_style(False)

    def set_active(self, active: bool):
        self.setChecked(active)
        self._apply_style(active)

    def _apply_style(self, active: bool):
        base = """
            text-align: left;
            padding: 8px 10px 8px 14px;
            font-size: 12px;
            border: none;
            border-left: 3px solid transparent;
            border-radius: 0px 10px 10px 0px;
        """
        if active:
            self.setStyleSheet(f"""
                QPushButton {{{base}
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #00A3FF33, stop:1 #7B61FF22);
                    color: {Colors.TEXT_PRIMARY};
                    border-left: 3px solid {Colors.NEON_BLUE};
                    font-weight: 700;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{{base}
                    background: transparent;
                    color: {Colors.TEXT_SECONDARY};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: #00A3FF11;
                    color: {Colors.TEXT_PRIMARY};
                }}
            """)


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(188)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SIDEBAR};
                border-right: 1px solid {Colors.BORDER};
                border-top-left-radius: 18px;
                border-bottom-left-radius: 18px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 10)
        layout.setSpacing(6)

        layout.addWidget(SidebarLogo())

        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 8px; letter-spacing: 2px; "
            f"padding: 2px 14px; font-weight: 700;"
        )
        layout.addWidget(nav_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        nav_host = QWidget()
        nav_host.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 0, 6, 0)
        nav_layout.setSpacing(3)

        self._buttons: dict[str, NavButton] = {}
        for key, icon, label in NAV_ITEMS:
            btn = NavButton(key, icon, label)
            btn.clicked.connect(lambda checked=False, k=key: self._select(k))
            self._buttons[key] = btn
            nav_layout.addWidget(btn)
        nav_layout.addStretch()

        scroll.setWidget(nav_host)
        layout.addWidget(scroll, stretch=1)

        status_card = GlassCard(radius=12)
        status_card.setMinimumHeight(88)
        status_card.setMaximumHeight(100)
        status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.setSpacing(6)
        status_title = QLabel("SYSTEM STATUS")
        status_title.setStyleSheet(ThemeManager.section_title())
        self.status_dot = QLabel("● Online")
        self.status_dot.setWordWrap(True)
        self.status_dot.setMinimumHeight(18)
        self.status_dot.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 11px; font-weight: 700;"
        )
        self.health_label = QLabel("Health: 100%")
        self.health_label.setWordWrap(True)
        self.health_label.setMinimumHeight(16)
        self.health_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.health_label)
        layout.addWidget(status_card)

        self._select("dashboard")

    def _select(self, key: str):
        for k, btn in self._buttons.items():
            btn.set_active(k == key)
        self.page_selected.emit(key)

    def set_assistant_status(self, online: bool, label: str = ""):
        text = label or ("Online" if online else "Offline")
        color = Colors.SUCCESS if online else Colors.DANGER
        self.status_dot.setText(f"● {text}")
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 700;")
