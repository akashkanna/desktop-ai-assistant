"""Premium top header with global search and status."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from ui.theme.theme_manager import Colors
from ui.components.base import IconButton
from ui.layout.responsive import Breakpoints


class HeaderBar(QFrame):
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    search_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(56)
        self.setMaximumHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(8, 16, 32, 0.95);
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 12, 8)
        layout.setSpacing(14)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        self.title = QLabel("JARVIS AI")
        self.title.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 900; letter-spacing: 3px;"
        )
        self.subtitle = QLabel("AI Operating System")
        self.subtitle.setStyleSheet(f"color: {Colors.NEON_BLUE}; font-size: 10px; font-weight: 600;")
        brand.addWidget(self.title)
        brand.addWidget(self.subtitle)
        layout.addLayout(brand)

        self.search = QLineEdit()
        self.search.setPlaceholderText("⌘  Global command search…")
        self.search.setMinimumWidth(200)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.returnPressed.connect(
            lambda: self.search_submitted.emit(self.search.text().strip())
        )
        layout.addWidget(self.search, stretch=1)

        self.status_widget = QWidget()
        status_col = QVBoxLayout(self.status_widget)
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(0)
        self.connection = QLabel("● Connected")
        self.connection.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 10px; font-weight: 700;"
        )
        self.user_label = QLabel("👤 User")
        self.user_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px;")
        status_col.addWidget(self.connection)
        status_col.addWidget(self.user_label)
        layout.addWidget(self.status_widget)

        self.notif = IconButton("🔔", "Notifications")
        layout.addWidget(self.notif)

        self.btn_min = IconButton("─", "Minimize")
        self.btn_max = IconButton("☐", "Maximize")
        self.btn_close = IconButton("✕", "Close", danger=True)
        self.btn_min.clicked.connect(self.minimize_clicked.emit)
        self.btn_max.clicked.connect(self.maximize_clicked.emit)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        narrow = self.width() < Breakpoints.COMPACT
        self.subtitle.setVisible(not narrow)
        self.status_widget.setVisible(not narrow)
        self.notif.setVisible(not narrow)

    def set_status(self, text: str, color: str = Colors.SUCCESS):
        self.connection.setText(f"● {text}")
        self.connection.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700;"
        )

    def set_waveform_active(self, active: bool):
        pass  # Waveform lives in hero + command dock
