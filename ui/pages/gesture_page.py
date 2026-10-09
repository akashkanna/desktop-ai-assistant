"""
Gesture Control Page.
Integrates the Jarvis futuristic gesture control panel into the dashboard pages.
"""

from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtCore import Qt
from ui.theme.theme_manager import Colors
from ui.components.base import PageShell, SectionHeader
from gesture_control.gesture_overlay import GestureDashboardPanel

class GesturePage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("background: transparent; border: none;")
        
        self.shell = PageShell()
        self.shell.layout_ref.addWidget(SectionHeader("Jarvis Gesture Control"))
        
        self.intro = QLabel(
            "Air-control touchless desktop interaction using MediaPipe hand gesture tracking. "
            "Control the mouse, click, drag, scroll, zoom, and wake the assistant from mid-air."
        )
        self.intro.setWordWrap(True)
        self.intro.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 14px; margin-bottom: 8px;")
        self.shell.layout_ref.addWidget(self.intro)
        
        self.dashboard_panel = GestureDashboardPanel()
        self.shell.layout_ref.addWidget(self.dashboard_panel)
        self.shell.layout_ref.addStretch()
        
        self.setWidget(self.shell)

    def wire_telemetry(self, gesture_controller):
        """Connects the telemetry updates from the gesture controller to the dashboard panel."""
        if hasattr(gesture_controller, "_manager"):
            gesture_controller._manager.telemetry_updated.connect(self.dashboard_panel.update_telemetry)
        else:
            # Direct compatibility fallback if we are given raw GestureManager
            gesture_controller.telemetry_updated.connect(self.dashboard_panel.update_telemetry)
