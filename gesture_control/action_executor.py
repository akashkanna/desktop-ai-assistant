"""
Action Executor module for Jarvis Gesture Control.
Translates gestures to PyAutoGUI shortcuts, Pycaw volume controls, and WMI brightness levels.
"""

import time
import subprocess
import pyautogui
from logger_config import setup_logger

logger = setup_logger("action_executor")

# PyAutoGUI settings
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

class ActionExecutor:
    def __init__(self):
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception:
            self.screen_width, self.screen_height = 1920, 1080
            
        self.last_cursor_pos = (self.screen_width // 2, self.screen_height // 2)
        
        # Scroll & Slide tracking
        self.scroll_velocity = 0.0
        self.last_scroll_y = None
        self.last_volume = 50
        self.last_brightness = 50
        
        # Pycaw audio controller initialization
        self.volume_interface = None
        self._init_pycaw()

    def _init_pycaw(self):
        """Initializes Pycaw Windows Core Audio API interface."""
        try:
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            self.volume_interface = devices.EndpointVolume
            logger.info("Pycaw Audio interface initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not load pycaw audio interface: {e}")

    def move_cursor(self, index_tip_coords, settings):
        """Moves cursor with smoothing, scaling workspace margins, and edge snapping."""
        tx, ty, _ = index_tip_coords
        
        # Bounding box in camera coordinates
        x_min, x_max = 0.25, 0.75
        y_min, y_max = 0.25, 0.75
        
        # Scale to box
        scaled_x = (tx - x_min) / (x_max - x_min)
        scaled_y = (ty - y_min) / (y_max - y_min)
        
        # Clamp to [0.0, 1.0]
        scaled_x = max(0.0, min(1.0, scaled_x))
        scaled_y = max(0.0, min(1.0, scaled_y))
        
        # Apply cursor sensitivity
        target_x = int(scaled_x * self.screen_width)
        target_y = int(scaled_y * self.screen_height)
        
        # Linear Interpolation
        curr_x, curr_y = self.last_cursor_pos
        alpha = 1.0 - settings.cursor_smoothing
        
        smoothed_x = int(curr_x + alpha * (target_x - curr_x))
        smoothed_y = int(curr_y + alpha * (target_y - curr_y))
        
        # Edge snapping
        margin = settings.edge_margin
        if smoothed_x < margin:
            smoothed_x = 0
        elif smoothed_x > self.screen_width - margin:
            smoothed_x = self.screen_width
            
        if smoothed_y < margin:
            smoothed_y = 0
        elif smoothed_y > self.screen_height - margin:
            smoothed_y = self.screen_height
            
        try:
            pyautogui.moveTo(smoothed_x, smoothed_y)
            self.last_cursor_pos = (smoothed_x, smoothed_y)
        except Exception as e:
            logger.error(f"Failed to move cursor: {e}")

    def execute_click(self, button="left"):
        try:
            if button == "left":
                pyautogui.click()
                logger.info("OS Shortcut: Left Click")
            elif button == "right":
                pyautogui.click(button="right")
                logger.info("OS Shortcut: Right Click")
            elif button == "double":
                pyautogui.doubleClick()
                logger.info("OS Shortcut: Double Click")
        except Exception as e:
            logger.error(f"Failed to click: {e}")

    def drag_start(self):
        try:
            pyautogui.mouseDown()
            logger.info("OS Shortcut: Drag Start")
        except Exception as e:
            logger.error(f"Drag start failed: {e}")

    def drag_end(self):
        try:
            pyautogui.mouseUp()
            logger.info("OS Shortcut: Drag End")
        except Exception as e:
            logger.error(f"Drag end failed: {e}")

    def execute_vertical_scroll(self, index_tip_coords, settings):
        """Scrolls vertically based on hand position change."""
        _, ty, _ = index_tip_coords
        
        if self.last_scroll_y is None:
            self.last_scroll_y = ty
            return
            
        dy = ty - self.last_scroll_y
        self.last_scroll_y = ty
        
        # Compute scroll delta
        scroll_amount = int(dy * self.screen_height * settings.scroll_sensitivity * 0.18)
        self.scroll_velocity = (1.0 - settings.scroll_smoothing) * scroll_amount + settings.scroll_smoothing * self.scroll_velocity
        
        if abs(self.scroll_velocity) >= 1.0:
            try:
                # Scroll down if dy > 0, scroll up if dy < 0
                pyautogui.scroll(int(-self.scroll_velocity * 10))
            except Exception as e:
                logger.error(f"Vertical scroll failed: {e}")

    def reset_scroll_tracking(self):
        self.last_scroll_y = None
        self.scroll_velocity = 0.0

    # SHORTCUTS MAPPINGS
    # ==========================================
    def execute_prev_desktop(self):
        """Win + Ctrl + Left -> Previous Virtual Desktop."""
        try:
            pyautogui.hotkey("win", "ctrl", "left")
            logger.info("OS Shortcut: Previous Virtual Desktop")
        except Exception as e:
            logger.error(f"Failed to execute Prev Desktop: {e}")

    def execute_next_desktop(self):
        """Win + Ctrl + Right -> Next Virtual Desktop."""
        try:
            pyautogui.hotkey("win", "ctrl", "right")
            logger.info("OS Shortcut: Next Virtual Desktop")
        except Exception as e:
            logger.error(f"Failed to execute Next Desktop: {e}")

    def execute_move_window_left_monitor(self):
        """Win + Shift + Left -> Move active window left."""
        try:
            pyautogui.hotkey("win", "shift", "left")
            logger.info("OS Shortcut: Move window to left monitor")
        except Exception as e:
            logger.error(f"Failed to move window left: {e}")

    def execute_move_window_right_monitor(self):
        """Win + Shift + Right -> Move active window right."""
        try:
            pyautogui.hotkey("win", "shift", "right")
            logger.info("OS Shortcut: Move window to right monitor")
        except Exception as e:
            logger.error(f"Failed to move window right: {e}")

    def execute_task_view(self):
        """Win + Tab -> Open Task View."""
        try:
            pyautogui.hotkey("win", "tab")
            logger.info("OS Shortcut: Opened Task View")
        except Exception as e:
            logger.error(f"Failed to open Task View: {e}")

    def execute_show_desktop(self):
        """Win + D -> Minimizes all windows / toggles Desktop."""
        try:
            pyautogui.hotkey("win", "d")
            logger.info("OS Shortcut: Show Desktop")
        except Exception as e:
            logger.error(f"Failed to Show Desktop: {e}")

    def execute_maximize_window(self):
        """Win + Up -> Maximize window."""
        try:
            pyautogui.hotkey("win", "up")
            logger.info("OS Shortcut: Maximize Window")
        except Exception as e:
            logger.error(f"Failed to Maximize Window: {e}")

    def execute_minimize_window(self):
        """Win + Down -> Minimize window."""
        try:
            pyautogui.hotkey("win", "down")
            logger.info("OS Shortcut: Minimize Window")
        except Exception as e:
            logger.error(f"Failed to Minimize Window: {e}")

    def execute_alt_tab(self):
        """Alt + Tab -> Swaps foreground app."""
        try:
            pyautogui.hotkey("alt", "tab")
            logger.info("OS Shortcut: Alt + Tab")
        except Exception as e:
            logger.error(f"Failed Alt + Tab: {e}")

    def execute_browser_back(self):
        """Alt + Left -> Browser Back Navigation."""
        try:
            pyautogui.hotkey("alt", "left")
            logger.info("OS Shortcut: Browser Back")
        except Exception as e:
            logger.error(f"Failed Browser Back: {e}")

    def execute_browser_forward(self):
        """Alt + Right -> Browser Forward Navigation."""
        try:
            pyautogui.hotkey("alt", "right")
            logger.info("OS Shortcut: Browser Forward")
        except Exception as e:
            logger.error(f"Failed Browser Forward: {e}")

    # ANALOGUE CONTROLS
    # ==========================================
    def execute_volume_slide(self, distance_ratio):
        """Sets Master Speaker Volume based on distance between Thumb and Index tip."""
        # Scale: distance_ratio typically in range [0.05, 0.22]
        min_d, max_d = 0.05, 0.22
        pct = (distance_ratio - min_d) / (max_d - min_d) * 100
        pct = max(0, min(100, int(pct)))
        
        # Avoid minor fluttering
        if abs(pct - self.last_volume) >= 3:
            self.last_volume = pct
            if self.volume_interface:
                try:
                    self.volume_interface.SetMasterVolumeLevelScalar(pct / 100.0, None)
                    logger.info(f"Volume set to {pct}%")
                except Exception as e:
                    logger.error(f"Failed to set Pycaw volume: {e}")
            else:
                # Fallback: PyAutoGUI volume adjustment hotkeys
                # (less precise but always works)
                pass

    def execute_brightness_slide(self, distance_ratio):
        """Sets Monitor Brightness based on distance between Thumb and Middle tip."""
        min_d, max_d = 0.05, 0.22
        pct = (distance_ratio - min_d) / (max_d - min_d) * 100
        pct = max(0, min(100, int(pct)))
        
        if abs(pct - self.last_brightness) >= 4:
            self.last_brightness = pct
            try:
                # Set Windows Brightness using WMI PowerShell command asynchronously
                cmd = f"Powershell ((Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{pct}))"
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
                logger.info(f"Brightness set to {pct}%")
            except Exception as e:
                logger.error(f"Failed to set Windows brightness: {e}")
