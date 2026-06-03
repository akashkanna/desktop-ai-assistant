"""Premium top header with global search, status, and window controls.

The header acts as the *custom title bar* — it forwards drag and
double-click events to the parent ``FramelessWindow`` so that window
management behaves exactly like a native Windows application.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QMouseEvent

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
        layout.setAlignment(Qt.AlignVCenter)

        brand = QVBoxLayout()
        brand.setAlignment(Qt.AlignVCenter)
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
        self.search.setMinimumWidth(160)
        self.search.setMinimumHeight(34)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.setStyleSheet(f"background: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; border-radius: 12px; padding: 0 12px; color: {Colors.TEXT_PRIMARY};")
        self.search.returnPressed.connect(
            lambda: self.search_submitted.emit(self.search.text().strip())
        )
        layout.addWidget(self.search, stretch=1)

        self.status_widget = QWidget()
        self.status_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        status_col = QVBoxLayout(self.status_widget)
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(0)
        status_col.setAlignment(Qt.AlignVCenter)
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

        # --- Drag state (forwarded to parent FramelessWindow) ---
        self._drag_pos = None

    # ------------------------------------------------------------------ #
    #  Responsive hide/show                                               #
    # ------------------------------------------------------------------ #
    def resizeEvent(self, event):
        super().resizeEvent(event)
        narrow = self.width() < Breakpoints.COMPACT
        self.subtitle.setVisible(not narrow)
        self.status_widget.setVisible(not narrow)
        self.notif.setVisible(not narrow)

    # ------------------------------------------------------------------ #
    #  Public helpers                                                      #
    # ------------------------------------------------------------------ #
    def set_status(self, text: str, color: str = Colors.SUCCESS):
        self.connection.setText(f"● {text}")
        self.connection.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700;"
        )

    def set_waveform_active(self, active: bool):
        pass  # Waveform lives in hero + command dock

    def update_maximize_icon(self, state: str):
        """
        Switch the maximize button between ☐ (maximize) and ❐ (restore)
        to reflect the current window state.

        Parameters
        ----------
        state : str
            One of ``"normal"``, ``"minimized"``, ``"maximized"``,
            ``"fullscreen"`` — emitted by ``FramelessWindow.window_state_changed``.
        """
        if state == "maximized":
            self.btn_max.setText("❐")
            self.btn_max.setToolTip("Restore")
        else:
            self.btn_max.setText("☐")
            self.btn_max.setToolTip("Maximize")

    # ------------------------------------------------------------------ #
    #  Title-bar drag forwarding                                          #
    #                                                                      #
    #  The header forwards mouse press / move / release to the parent     #
    #  FramelessWindow so that dragging the title bar moves the window.   #
    # ------------------------------------------------------------------ #
    def _frameless_parent(self):
        """Walk the parent chain to find the FramelessWindow."""
        from ui.components.base import FramelessWindow
        p = self.parent()
        while p is not None:
            if isinstance(p, FramelessWindow):
                return p
            p = p.parent()
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            win = self._frameless_parent()
            if win:
                self._drag_pos = (
                    event.globalPosition().toPoint()
                    - win.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (event.buttons() & Qt.LeftButton) and self._drag_pos is not None:
            win = self._frameless_parent()
            if win:
                from ui.components.base import WindowState
                if win.win_state == WindowState.MAXIMIZED:
                    # Snap-out: restore window and reposition under cursor
                    old_width = win.width()
                    win.restore_normal()
                    new_width = win.width()
                    ratio = self._drag_pos.x() / max(old_width, 1)
                    new_x = int(ratio * new_width)
                    cursor_global = event.globalPosition().toPoint()
                    win.move(
                        cursor_global.x() - new_x,
                        cursor_global.y() - self._drag_pos.y(),
                    )
                    self._drag_pos.setX(new_x)
                else:
                    win.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click the title bar area to toggle maximize / restore."""
        if event.button() == Qt.LeftButton:
            self.maximize_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

