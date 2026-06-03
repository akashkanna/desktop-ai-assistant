"""Premium futuristic AI operating system sidebar with animated logo and status indicators."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, 
    QScrollArea, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Signal, Qt, QPropertyAnimation, QEasingCurve, QEvent, QTimer, 
    QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import QColor, QFont

from ui.theme.theme_manager import Colors, ThemeManager
from ui.animations.effects import apply_glow


# Navigation structure with grouped sections
NAV_SECTIONS = {
    "CORE": [
        ("dashboard", "◉", "Dashboard"),
        ("voice", "🎙", "Voice Assistant"),
        ("gesture", "✋", "Gesture Control"),
    ],
    "AUTOMATION": [
        ("workflow", "⚡", "Workflow"),
        ("apps", "▦", "App Launcher"),
        ("browser", "🌐", "Browser Control"),
    ],
    "SYSTEM": [
        ("system", "⚙", "System Control"),
        ("files", "📁", "Files & Folders"),
        ("screenshots", "📷", "Screenshots"),
    ],
    "SETTINGS": [
        ("memory", "🧠", "AI Memory"),
        ("logs", "📋", "Logs"),
        ("settings", "🔧", "Settings"),
    ],
}

# Status indicators mapping
STATUS_INDICATORS = {
    "voice": ("🎙", "Voice", Colors.NEON_BLUE),
    "gesture": ("✋", "Gesture", Colors.NEON_CYAN),
    "memory": ("🧠", "Memory", Colors.NEON_PURPLE),
    "ai_core": ("◈", "AI Core", Colors.NEON_GREEN),
}


class AnimatedJarvisLogo(QWidget):
    """Animated Jarvis logo at the top of the sidebar."""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(90)
        self.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Main logo ring
        self.logo_ring = QLabel("J")
        self.logo_ring.setFixedSize(56, 56)
        self.logo_ring.setAlignment(Qt.AlignCenter)
        self.logo_ring.setFont(QFont("Rajdhani", 28, QFont.Bold))
        self.logo_ring.setStyleSheet(f"""
            background: radial-gradient(circle at 30% 30%, #1A3A52, #0A1520);
            border: 2.5px solid {Colors.NEON_BLUE};
            border-radius: 28px;
            color: {Colors.NEON_BLUE};
            font-weight: 900;
        """)
        layout.addWidget(self.logo_ring, alignment=Qt.AlignCenter)
        
        # Apply glow effect
        apply_glow(self.logo_ring, Colors.NEON_BLUE, blur=32, alpha=200)
        
        # Subtitle
        subtitle = QLabel("JARVIS OS")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Inter", 8, QFont.Bold))
        subtitle.setStyleSheet(f"""
            color: {Colors.NEON_BLUE};
            letter-spacing: 3px;
            background: transparent;
        """)
        layout.addWidget(subtitle)
        
        # Pulse animation
        self._setup_pulse_animation()
    
    def _setup_pulse_animation(self):
        """Setup continuous pulse animation for the logo."""
        self.pulse_anim = QPropertyAnimation(self.logo_ring, b"opacity")
        self.pulse_anim.setDuration(2000)
        self.pulse_anim.setStartValue(0.7)
        self.pulse_anim.setEndValue(1.0)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_anim.setLoopCount(-1)
        
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.85)
        self.logo_ring.setGraphicsEffect(opacity_effect)
        
        # Animate the effect
        self.pulse_effect_anim = QPropertyAnimation(opacity_effect, b"opacity")
        self.pulse_effect_anim.setDuration(2000)
        self.pulse_effect_anim.setStartValue(0.6)
        self.pulse_effect_anim.setEndValue(1.0)
        self.pulse_effect_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_effect_anim.setLoopCount(-1)
        self.pulse_effect_anim.start()


class GlowingIconButton(QPushButton):
    """Premium nav button with glowing container icon."""
    
    def __init__(self, key: str, icon: str, label: str):
        super().__init__()
        self.page_key = key
        self.icon_char = icon
        self.label_text = label
        self._is_active = False
        self._is_collapsed = False
        
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self._update_style()
    
    def set_active(self, active: bool):
        """Update button to active/inactive state."""
        self._is_active = active
        self._update_style()
    
    def set_collapsed(self, collapsed: bool):
        """Update button for collapsed/expanded state."""
        self._is_collapsed = collapsed
        self._update_style()
    
    def _update_style(self):
        """Apply styling based on state."""
        if self._is_collapsed:
            # Collapsed mode: icon only
            self.setText(self.icon_char)
            text_size = "24px"
            padding = "12px"
        else:
            # Expanded mode: icon and label
            self.setText(f"{self.icon_char}  {self.label_text}")
            text_size = "12px"
            padding = "8px 12px"
        
        if self._is_active:
            # Active state with neon glow
            style = f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(0, 163, 255, 0.25),
                        stop:1 rgba(123, 97, 255, 0.15)
                    );
                    color: {Colors.NEON_BLUE};
                    border: 2px solid {Colors.NEON_BLUE};
                    border-left: 4px solid {Colors.NEON_BLUE};
                    border-radius: 16px;
                    padding: {padding};
                    font-size: {text_size};
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(0, 163, 255, 0.35),
                        stop:1 rgba(123, 97, 255, 0.25)
                    );
                    border: 2px solid {Colors.NEON_BLUE};
                }}
            """
        else:
            # Inactive state
            style = f"""
                QPushButton {{
                    background: rgba(20, 35, 70, 0.4);
                    color: {Colors.TEXT_SECONDARY};
                    border: 2px solid rgba(26, 39, 68, 0.8);
                    border-radius: 16px;
                    padding: {padding};
                    font-size: {text_size};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: rgba(30, 50, 90, 0.6);
                    border: 2px solid {Colors.NEON_BLUE};
                    color: {Colors.NEON_BLUE};
                }}
            """
        
        self.setStyleSheet(style)


class SectionHeader(QLabel):
    """Styled section header for navigation groups."""
    
    def __init__(self, title: str, color: str = Colors.NEON_BLUE):
        super().__init__(title)
        self.setStyleSheet(f"""
            color: {color};
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 2.5px;
            padding: 12px 14px 6px 14px;
            background: transparent;
        """)
        self.setFont(QFont("Rajdhani", 9, QFont.Bold))


class StatusIndicator(QFrame):
    """Status indicator widget for system components."""
    
    def __init__(self, icon: str, label: str, color: str):
        super().__init__()
        self.color = color
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setFixedWidth(12)
        self.status_dot.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: 900;
        """)
        layout.addWidget(self.status_dot)
        
        # Label
        label_widget = QLabel(f"{icon} {label}")
        label_widget.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 10px;
            font-weight: 600;
            background: transparent;
        """)
        layout.addWidget(label_widget)
        layout.addStretch()
    
    def set_active(self, active: bool):
        """Update indicator status."""
        color = self.color if active else Colors.TEXT_MUTED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 900;")


class StatusPanel(QFrame):
    """Compact status panel showing system indicators."""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10, 20, 40, 0.6),
                    stop:1 rgba(20, 30, 50, 0.4)
                );
                border: 1px solid {Colors.BORDER};
                border-radius: 14px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Title
        title = QLabel("SYSTEM STATUS")
        title.setFont(QFont("Rajdhani", 9, QFont.Bold))
        title.setStyleSheet(f"""
            color: {Colors.NEON_BLUE};
            letter-spacing: 1.5px;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Status indicators
        self.indicators: dict[str, StatusIndicator] = {}
        for key, (icon, label, color) in STATUS_INDICATORS.items():
            indicator = StatusIndicator(icon, label, color)
            self.indicators[key] = indicator
            layout.addWidget(indicator)
        
        layout.addSpacing(2)
    
    def set_indicator_status(self, key: str, active: bool):
        """Update indicator status."""
        if key in self.indicators:
            self.indicators[key].set_active(active)


class PremiumSidebar(QFrame):
    """Premium futuristic sidebar with animated logo, grouped sections, and status indicators."""
    
    page_selected = Signal(str)
    collapsed_changed = Signal(bool)
    
    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 80
    
    def __init__(self):
        super().__init__()
        self._collapsed = False
        self._anim_group = None
        
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(
                    180deg,
                    {Colors.BG_SIDEBAR} 0%,
                    #050910 100%
                );
                border-right: 1px solid {Colors.BORDER};
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with logo and collapse button
        header = self._create_header()
        layout.addWidget(header)
        
        # Scrollable navigation
        scroll = self._create_nav_scroll()
        layout.addWidget(scroll, stretch=1)
        
        # Status panel
        self.status_panel = StatusPanel()
        layout.addWidget(self.status_panel)
        
        # Bottom spacer
        layout.addSpacing(8)
    
    def _create_header(self) -> QWidget:
        """Create header with animated logo and collapse button."""
        header = QFrame()
        header.setStyleSheet("background: transparent; border: none;")
        header.setFixedHeight(110)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)
        
        # Animated logo
        self.logo = AnimatedJarvisLogo()
        layout.addWidget(self.logo)
        
        # Collapse button
        self.collapse_btn = QPushButton("━")
        self.collapse_btn.setFixedSize(40, 40)
        self.collapse_btn.setFont(QFont("Rajdhani", 14, QFont.Bold))
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(30, 50, 90, 0.4);
                color: {Colors.NEON_BLUE};
                border: 1.5px solid {Colors.BORDER};
                border-radius: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: rgba(40, 60, 110, 0.6);
                border: 1.5px solid {Colors.NEON_BLUE};
            }}
            QPushButton:pressed {{
                background: rgba(50, 70, 130, 0.8);
            }}
        """)
        layout.addWidget(self.collapse_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        
        return header
    
    def _create_nav_scroll(self) -> QScrollArea:
        """Create scrollable navigation area with grouped sections."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        nav_host = QWidget()
        nav_host.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(0)
        
        # Create buttons storage
        self._buttons: dict[str, GlowingIconButton] = {}
        
        # Color mapping for section headers
        section_colors = {
            "CORE": Colors.NEON_BLUE,
            "AUTOMATION": Colors.NEON_PURPLE,
            "SYSTEM": Colors.NEON_CYAN,
            "SETTINGS": Colors.NEON_ORANGE,
        }
        
        # Build navigation sections
        for section_name, items in NAV_SECTIONS.items():
            # Section header
            header = SectionHeader(section_name, section_colors.get(section_name, Colors.NEON_BLUE))
            nav_layout.addWidget(header)
            
            # Navigation buttons
            for key, icon, label in items:
                btn = GlowingIconButton(key, icon, label)
                btn.clicked.connect(lambda checked=False, k=key: self._select(k))
                self._buttons[key] = btn
                nav_layout.addWidget(btn)
            
            # Spacing between sections
            nav_layout.addSpacing(4)
        
        nav_layout.addStretch()
        scroll.setWidget(nav_host)
        return scroll
    
    def toggle_collapsed(self):
        """Animate sidebar collapse/expand."""
        self._collapsed = not self._collapsed
        target_width = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH
        
        # Update button text
        self.collapse_btn.setText("←" if self._collapsed else "→")
        
        # Update all buttons
        for btn in self._buttons.values():
            btn.set_collapsed(self._collapsed)
        
        # Hide/show logo and panel
        self.logo.setVisible(not self._collapsed)
        self.status_panel.setVisible(not self._collapsed)
        
        # Animate width
        if self._anim_group:
            self._anim_group.stop()
        
        self._anim_group = QPropertyAnimation(self, b"minimumWidth")
        self._anim_group.setDuration(300)
        self._anim_group.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_group.setEndValue(target_width)
        self._anim_group.start()
        
        self.setFixedWidth(target_width)
        self.collapsed_changed.emit(self._collapsed)
    
    def _select(self, key: str):
        """Select navigation item."""
        for k, btn in self._buttons.items():
            btn.set_active(k == key)
        self.page_selected.emit(key)
    
    def set_page(self, page_key: str):
        """Programmatically select a page."""
        self._select(page_key)
    
    def set_indicator_status(self, indicator_key: str, active: bool):
        """Update status indicator (voice, gesture, memory, ai_core)."""
        self.status_panel.set_indicator_status(indicator_key, active)
    
    def set_assistant_status(self, online: bool, label: str = ""):
        """Set overall assistant status (shown in status panel if needed)."""
        # Could add an overall status indicator here
        pass
