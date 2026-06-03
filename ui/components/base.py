"""Base widgets used across the Jarvis OS interface."""

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QMainWindow, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

from ui.theme.theme_manager import Colors, ThemeManager


class FramelessWindow(QMainWindow):
    """Draggable frameless window shell."""

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


class GlassCard(QFrame):
    """Glassmorphism panel — border highlight on hover (no shadow bleed)."""

    def __init__(self, parent=None, radius: int = 16, glow: bool = False):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self._radius = radius
        self._glow = glow
        self._apply_style(False)
        self.setAttribute(Qt.WA_Hover, True)

    def _apply_style(self, hovered: bool):
        border = Colors.NEON_BLUE if hovered and self._glow else Colors.BORDER
        bg = Colors.BG_CARD_HOVER if hovered and self._glow else Colors.BG_CARD
        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {self._radius}px;
            }}
        """)

    def enterEvent(self, event):
        if self._glow:
            self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._glow:
            self._apply_style(False)
        super().leaveEvent(event)


class SectionHeader(QLabel):
    def __init__(self, text: str, purple: bool = False, parent=None):
        super().__init__(text.upper(), parent)
        style = ThemeManager.purple_section_title() if purple else ThemeManager.section_title()
        self.setStyleSheet(style)


class IconButton(QPushButton):
    def __init__(self, icon: str, tooltip: str = "", size: int = 34, danger: bool = False):
        super().__init__(icon)
        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        hover_bg = "#FF2E6333" if danger else "#00A3FF22"
        hover_color = Colors.DANGER if danger else Colors.NEON_BLUE
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {size // 2}px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {hover_color};
                border-color: {hover_color};
            }}
        """)


class PageShell(QFrame):
    """Scrollable page container."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(16)

    @property
    def layout_ref(self):
        return self._layout
