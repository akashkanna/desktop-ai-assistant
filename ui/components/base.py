"""Base widgets used across the Jarvis OS interface."""

import sys
import enum
from ctypes import windll, byref, sizeof, c_int  # Windows-only; guarded below

from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QMainWindow, QVBoxLayout, QApplication, QWidget,
)
from PySide6.QtCore import Qt, Signal, QByteArray, QPoint
from PySide6.QtGui import QMouseEvent

from ui.theme.theme_manager import Colors, ThemeManager


# ---------------------------------------------------------------------------
#  Window state enum — single source of truth for the window lifecycle.
# ---------------------------------------------------------------------------
class WindowState(enum.Enum):
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    FULLSCREEN = "fullscreen"


# ---------------------------------------------------------------------------
#  Win32 constants used to patch the native window style so that the OS
#  taskbar animations (minimize/maximize) work even on a frameless window.
# ---------------------------------------------------------------------------
_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import ctypes
    import ctypes.wintypes as wintypes

    # Window-style bits we need to add
    GWL_STYLE = -16
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_SYSMENU = 0x00080000
    WS_THICKFRAME = 0x00040000
    WS_CAPTION = 0x00C00000

    # Messages
    WM_NCCALCSIZE = 0x0083
    WM_NCHITTEST = 0x0084

    # Hit-test result codes
    HTCLIENT = 1
    HTCAPTION = 2
    HTLEFT = 10
    HTRIGHT = 11
    HTTOP = 12
    HTTOPLEFT = 13
    HTTOPRIGHT = 14
    HTBOTTOM = 15
    HTBOTTOMLEFT = 16
    HTBOTTOMRIGHT = 17

    GetWindowLongW = windll.user32.GetWindowLongW
    SetWindowLongW = windll.user32.SetWindowLongW


class FramelessWindow(QMainWindow):
    """
    Draggable frameless window with **native** minimize / maximize support.

    Key design decisions
    --------------------
    * A `WindowState` enum is the single source of truth.
    * On Windows we patch the native window style with WS_MINIMIZEBOX,
      WS_MAXIMIZEBOX, WS_THICKFRAME and WS_SYSMENU so the OS animates
      minimize / maximize transitions and the taskbar entry works correctly.
    * `WM_NCCALCSIZE` is intercepted so Windows does *not* draw its own
      non-client border (we keep our custom look).
    * Before maximizing we save `_normal_geometry`; on restore we use it
      for pixel-perfect return.
    * Dragging while maximized performs a "snap-out": the window restores
      to its normal size and repositions so the cursor is at the same
      proportional X position within the title bar.

    Signals
    -------
    window_state_changed(str)
        Emitted whenever the window state changes.  The payload is one of
        ``"normal"``, ``"minimized"``, ``"maximized"``, ``"fullscreen"``.
    """

    window_state_changed = Signal(str)

    def __init__(self):
        super().__init__()

        # --- Qt flags: frameless, but still a proper OS-level window -------
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- Internal state ------------------------------------------------
        self._win_state = WindowState.NORMAL
        self._drag_pos = None  # QPoint or None; non-None while dragging
        self._normal_geometry = None  # saved before maximizing

        # --- Windows-specific native style patch ---------------------------
        if _IS_WINDOWS:
            # Defer to the first show so that the HWND exists.
            self._native_patched = False

    # ------------------------------------------------------------------ #
    #  Windows native integration                                         #
    # ------------------------------------------------------------------ #
    def showEvent(self, event):
        """Patch native window style *once* on first show."""
        super().showEvent(event)
        if _IS_WINDOWS and not self._native_patched:
            hwnd = int(self.winId())
            style = GetWindowLongW(hwnd, GWL_STYLE)
            # Add minimize / maximize / resize / system-menu bits.
            style |= (
                WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_THICKFRAME | WS_SYSMENU
            )
            SetWindowLongW(hwnd, GWL_STYLE, style)
            self._native_patched = True

    def nativeEvent(self, event_type: QByteArray, message: int):
        """
        Intercept Windows messages so the OS knows our window is custom.

        * **WM_NCCALCSIZE** → return 0 so Windows does not add its default
          non-client border (we draw our own rounded frame).
        """
        if _IS_WINDOWS and event_type == b"windows_generic_MSG":
            try:
                import ctypes
                msg = ctypes.wintypes.MSG.from_address(int(message))

                if msg.message == WM_NCCALCSIZE and msg.wParam:
                    # Tell Windows: "I have zero non-client area."
                    return True, 0

                if msg.message == WM_NCHITTEST:
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    global_pos = QPoint(x, y)
                    local_pos = self.mapFromGlobal(global_pos)
                    width = self.width()
                    height = self.height()
                    border = 8

                    top = local_pos.y() < border
                    bottom = local_pos.y() >= height - border
                    left = local_pos.x() < border
                    right = local_pos.x() >= width - border

                    if top and left:
                        return True, HTTOPLEFT
                    if top and right:
                        return True, HTTOPRIGHT
                    if bottom and left:
                        return True, HTBOTTOMLEFT
                    if bottom and right:
                        return True, HTBOTTOMRIGHT
                    if left:
                        return True, HTLEFT
                    if right:
                        return True, HTRIGHT
                    if top:
                        return True, HTTOP
                    if bottom:
                        return True, HTBOTTOM
            except Exception:
                pass  # Fail silently — fall back to default Qt handling
        return super().nativeEvent(event_type, message)

    # ------------------------------------------------------------------ #
    #  Centralised state transitions                                      #
    # ------------------------------------------------------------------ #
    def _set_state(self, new_state: WindowState):
        """Transition to *new_state* and emit the change signal."""
        if self._win_state == new_state:
            return
        self._win_state = new_state
        self.window_state_changed.emit(new_state.value)

    @property
    def win_state(self) -> WindowState:
        return self._win_state

    # ------------------------------------------------------------------ #
    #  Public actions (called from header / main_window)                  #
    # ------------------------------------------------------------------ #
    def minimize(self):
        """Send the window to the taskbar."""
        self._set_state(WindowState.MINIMIZED)
        self.showMinimized()

    def toggle_maximize(self):
        """Toggle between MAXIMIZED and NORMAL (with geometry restore)."""
        if self._win_state == WindowState.MAXIMIZED:
            self.restore_normal()
        else:
            self.maximize()

    def _refresh_layouts(self):
        """Force Qt to recalculate layouts and repaint after state changes."""
        def refresh(widget: QWidget):
            layout = widget.layout()
            if layout:
                layout.invalidate()
                try:
                    layout.activate()
                except Exception:
                    pass
            widget.updateGeometry()
            widget.update()
            for child in widget.findChildren(QWidget):
                child_layout = child.layout()
                if child_layout:
                    child_layout.invalidate()
                    try:
                        child_layout.activate()
                    except Exception:
                        pass
                child.updateGeometry()
                child.update()

        refresh(self)

    def maximize(self):
        """
        Maximize using native window state so the OS and our custom
        title-bar stay synchronized.
        """
        if self._win_state != WindowState.MAXIMIZED:
            self._normal_geometry = self.geometry()
        self.showMaximized()
        self._set_state(WindowState.MAXIMIZED)

    def restore_normal(self):
        """Restore to the previously saved normal-mode geometry."""
        self.showNormal()
        if self._win_state == WindowState.MAXIMIZED and self._normal_geometry is not None:
            self.setGeometry(self._normal_geometry)
        self._set_state(WindowState.NORMAL)
        self._refresh_layouts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._win_state == WindowState.NORMAL:
            self._normal_geometry = self.geometry()
        self._refresh_layouts()

    # ------------------------------------------------------------------ #
    #  Mouse-driven window dragging + snap-out                            #
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.LeftButton) or self._drag_pos is None:
            return

        if self._win_state == WindowState.MAXIMIZED:
            # --- Snap-out: restore and reposition under cursor -----------
            old_width = self.width()
            self.restore_normal()
            new_width = self.width()

            # Keep the cursor at the same proportional X within the bar.
            ratio = self._drag_pos.x() / max(old_width, 1)
            new_x = int(ratio * new_width)
            cursor_global = event.globalPosition().toPoint()
            self.move(cursor_global.x() - new_x, cursor_global.y() - self._drag_pos.y())
            self._drag_pos.setX(new_x)
        else:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Clear drag anchor so no ghost-dragging occurs."""
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click on the window body toggles maximize / restore."""
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
            event.accept()

    # ------------------------------------------------------------------ #
    #  Qt change-event hook — keep our enum in sync with OS-level changes #
    # ------------------------------------------------------------------ #
    def changeEvent(self, event):
        """
        Catch OS-initiated state changes (e.g. user clicks taskbar icon to
        un-minimize) and sync our `WindowState` enum accordingly.
        """
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            qt_state = self.windowState()
            if qt_state & Qt.WindowMinimized:
                self._set_state(WindowState.MINIMIZED)
            elif qt_state & Qt.WindowMaximized:
                self._set_state(WindowState.MAXIMIZED)
            elif qt_state & Qt.WindowFullScreen:
                self._set_state(WindowState.FULLSCREEN)
            else:
                self._set_state(WindowState.NORMAL)

            if self._win_state in (WindowState.NORMAL, WindowState.MAXIMIZED):
                self._refresh_layouts()


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
