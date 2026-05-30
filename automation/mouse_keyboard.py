"""
mouse_keyboard.py
Handles mouse movement, clicking, typing, and keyboard shortcuts.
"""

import logging
import time

logger = logging.getLogger(__name__)


class MouseKeyboardController:
    """Controls mouse and keyboard for desktop automation."""

    def __init__(self):
        try:
            import pyautogui
            self._pyautogui = pyautogui
            pyautogui.FAILSAFE = True   # Move mouse to corner to abort
            pyautogui.PAUSE = 0.1       # Small pause between actions
        except ImportError:
            self._pyautogui = None
            logger.warning("pyautogui not available. Mouse/keyboard control disabled.")

    def type_text(self, text: str) -> tuple[bool, str]:
        """Type text at current cursor position."""
        if not self._pyautogui:
            return False, "Keyboard control is not available."
        try:
            self._pyautogui.typewrite(text, interval=0.05)
            return True, f"Typed: '{text}'"
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return False, "I couldn't type the text."

    def press_shortcut(self, shortcut: str) -> tuple[bool, str]:
        """
        Press a keyboard shortcut.
        Format: 'ctrl+c', 'alt+f4', 'ctrl+shift+t'
        """
        if not self._pyautogui:
            return False, "Keyboard control is not available."
        try:
            keys = [k.strip() for k in shortcut.lower().split("+")]
            self._pyautogui.hotkey(*keys)
            return True, f"Pressed {shortcut}."
        except Exception as e:
            logger.error(f"Shortcut failed: {e}")
            return False, f"I couldn't press {shortcut}."

    def click(self, x: int = None, y: int = None, button: str = "left") -> tuple[bool, str]:
        """Click at coordinates or current position."""
        if not self._pyautogui:
            return False, "Mouse control is not available."
        try:
            if x is not None and y is not None:
                self._pyautogui.click(x, y, button=button)
            else:
                self._pyautogui.click(button=button)
            return True, "Clicked."
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False, "I couldn't perform the click."

    def take_screenshot(self, save_path: str = None) -> tuple[bool, str]:
        """Take a screenshot and optionally save it."""
        if not self._pyautogui:
            return False, "Screenshot is not available."
        try:
            import os
            from datetime import datetime
            screenshot = self._pyautogui.screenshot()

            if not save_path:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.expanduser(f"~/Desktop/screenshot_{ts}.png")

            screenshot.save(save_path)
            return True, f"Screenshot saved to {save_path}."
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False, "I couldn't take a screenshot."

    def scroll(self, amount: int = 3, direction: str = "down") -> tuple[bool, str]:
        """Scroll the page."""
        if not self._pyautogui:
            return False, "Scroll is not available."
        try:
            clicks = -amount if direction == "down" else amount
            self._pyautogui.scroll(clicks)
            return True, f"Scrolled {direction}."
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False, "I couldn't scroll."

    def close_window(self) -> tuple[bool, str]:
        """Close the current active window."""
        import sys
        try:
            if sys.platform == "win32":
                return self.press_shortcut("alt+f4")
            else:
                return self.press_shortcut("ctrl+w")
        except Exception as e:
            return False, "I couldn't close the window."
