"""Glass styling helpers — rgba glassmorphism."""

from ui.theme.theme_manager import Colors, ThemeManager

__all__ = ["Colors", "ThemeManager", "glass_style"]


def glass_style(radius: int = 18, highlight: bool = False) -> str:
    border = Colors.NEON_BLUE if highlight else Colors.BORDER
    return f"""
        background-color: rgba(10, 20, 40, 0.65);
        border: 1px solid {border};
        border-radius: {radius}px;
    """
