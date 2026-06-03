"""Central theme definitions and QSS stylesheet for Jarvis AI OS."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    BG_PRIMARY = "#050B1A"
    BG_SECONDARY = "#0A1228"
    BG_CARD = "#0D1529"
    BG_CARD_HOVER = "#121D38"
    BG_SIDEBAR = "#070E1F"
    BG_INPUT = "#0B1428"

    NEON_BLUE = "#00A3FF"
    NEON_PURPLE = "#7B61FF"
    NEON_CYAN = "#00FFD1"
    NEON_PINK = "#FF2E63"
    NEON_GREEN = "#00E676"
    NEON_ORANGE = "#FF9F43"
    NEON_YELLOW = "#FFD93D"

    TEXT_PRIMARY = "#F0F4FF"
    TEXT_SECONDARY = "#8B9DC3"
    TEXT_MUTED = "#5A6B8C"

    BORDER = "#1A2744"
    BORDER_GLOW = "#00A3FF44"
    GLASS = "#0D152980"

    SUCCESS = "#00E676"
    WARNING = "#FFD93D"
    DANGER = "#FF2E63"
    INFO = "#00A3FF"


class ThemeManager:
    """Applies global styles and provides reusable QSS fragments."""

    FONT_FAMILY = "'Segoe UI', 'Inter', 'Rajdhani', sans-serif"

    @classmethod
    def global_stylesheet(cls) -> str:
        c = Colors
        return f"""
        * {{
            font-family: {cls.FONT_FAMILY};
            color: {c.TEXT_PRIMARY};
        }}

        QWidget#RootFrame {{
            background-color: {c.BG_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 18px;
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            margin: 4px 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {c.BORDER};
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.BORDER};
            border-radius: 3px;
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c.BG_INPUT};
            border: 1px solid {c.BORDER};
            border-radius: 14px;
            padding: 8px 14px;
            min-height: 34px;
            color: {c.TEXT_PRIMARY};
            font-size: 13px;
            selection-background-color: {c.NEON_BLUE};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {c.NEON_BLUE};
        }}

        QComboBox {{
            background-color: {c.BG_INPUT};
            border: 1px solid {c.BORDER};
            border-radius: 12px;
            padding: 8px 12px;
            color: {c.TEXT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c.BG_CARD};
            border: 1px solid {c.BORDER};
            selection-background-color: {c.NEON_BLUE};
            color: {c.TEXT_PRIMARY};
        }}

        QSlider::groove:horizontal {{
            border-radius: 4px;
            height: 6px;
            background: {c.BORDER};
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {c.NEON_BLUE}, stop:1 {c.NEON_PURPLE});
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: white;
            border: 2px solid {c.NEON_BLUE};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}

        QToolTip {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.NEON_BLUE};
            border-radius: 8px;
            padding: 6px 10px;
        }}
        """

    @classmethod
    def glass_card(cls, radius: int = 16) -> str:
        c = Colors
        return f"""
            background-color: {c.BG_CARD};
            border: 1px solid {c.BORDER};
            border-radius: {radius}px;
        """

    @classmethod
    def gradient_button(cls, danger: bool = False) -> str:
        c = Colors
        if danger:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FF2E63, stop:1 #FF6B35);
                    color: white;
                    border: none;
                    border-radius: 14px;
                    padding: 10px 18px;
                    font-weight: 700;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FF4477, stop:1 #FF8055);
                }}
            """
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c.NEON_BLUE}, stop:1 {c.NEON_PURPLE});
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px 18px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #33B5FF, stop:1 #9580FF);
            }}
            QPushButton:disabled {{
                background: {c.BORDER};
                color: {c.TEXT_MUTED};
            }}
        """

    @classmethod
    def ghost_button(cls) -> str:
        c = Colors
        return f"""
            QPushButton {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 14px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {c.NEON_BLUE};
                background-color: {c.BG_CARD_HOVER};
            }}
        """

    @classmethod
    def section_title(cls) -> str:
        return f"""
            color: {Colors.NEON_BLUE};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
        """

    @classmethod
    def purple_section_title(cls) -> str:
        return f"""
            color: {Colors.NEON_PURPLE};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
        """
