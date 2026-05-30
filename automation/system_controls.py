"""
System Controls — Volume, Window Management, Brightness.
Uses pycaw for audio and pygetwindow / win32gui for window management.
"""
import subprocess
import ctypes
import os
from logger_config import setup_logger

logger = setup_logger("system_controls")


# ──────────────────────────────────────────────
# Volume Control
# ──────────────────────────────────────────────

def _get_volume_interface():
    try:
        import pythoncom
        pythoncom.CoInitialize()
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        logger.error(f"pycaw unavailable: {e}")
        return None


def get_volume() -> int:
    """Return current master volume as 0-100 int."""
    vol = _get_volume_interface()
    if vol:
        # getVolumeRange returns (min_dB, max_dB, increment)
        level = vol.GetMasterVolumeLevelScalar()
        return int(level * 100)
    return -1


def set_volume(level: int) -> str:
    """Set master volume to `level` (0-100)."""
    level = max(0, min(100, level))
    vol = _get_volume_interface()
    if vol:
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent."
    
    # Fallback: spam volume down to 0, then volume up to target
    try:
        import win32api
        import win32con
        # 50 presses of volume down ensures we hit 0
        for _ in range(50):
            win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        # Each volume up is typically 2%
        presses = level // 2
        for _ in range(presses):
            win32api.keybd_event(win32con.VK_VOLUME_UP, 0, 0, 0)
            win32api.keybd_event(win32con.VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP, 0)
        return f"Volume set to {level} percent."
    except Exception:
        return "I could not change the volume on your system."


def increase_volume(amount: int = 10) -> str:
    cur = get_volume()
    if cur == -1:
        try:
            import win32api, win32con
            for _ in range(amount // 2):
                win32api.keybd_event(win32con.VK_VOLUME_UP, 0, 0, 0)
                win32api.keybd_event(win32con.VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP, 0)
            return "Volume increased."
        except Exception:
            return "I could not increase the volume."
    new = min(100, cur + amount)
    return set_volume(new)


def decrease_volume(amount: int = 10) -> str:
    cur = get_volume()
    if cur == -1:
        try:
            import win32api, win32con
            for _ in range(amount // 2):
                win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, 0, 0)
                win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
            return "Volume decreased."
        except Exception:
            return "I could not decrease the volume."
    new = max(0, cur - amount)
    return set_volume(new)


def mute_volume() -> str:
    vol = _get_volume_interface()
    if vol:
        vol.SetMute(1, None)
        return "System volume muted."
    return "I could not mute the volume."


def unmute_volume() -> str:
    vol = _get_volume_interface()
    if vol:
        vol.SetMute(0, None)
        return "System volume unmuted."
    return "I could not unmute the volume."


# ──────────────────────────────────────────────
# Window Management
# ──────────────────────────────────────────────

def _get_active_hwnd():
    try:
        import win32gui
        return win32gui.GetForegroundWindow()
    except Exception:
        return None


def minimize_window(app_name: str = None) -> str:
    """Minimize the foreground window or a named application window."""
    try:
        import win32gui
        import win32con

        if app_name:
            def _enum_cb(hwnd, results):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name.lower() in title and win32gui.IsWindowVisible(hwnd):
                    results.append(hwnd)

            results = []
            win32gui.EnumWindows(_enum_cb, results)
            if results:
                win32gui.ShowWindow(results[0], win32con.SW_MINIMIZE)
                return f"Minimized {app_name}."
            return f"I could not find a window for {app_name}."
        else:
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return "Window minimized."
    except Exception as e:
        logger.error(f"minimize_window error: {e}")
        return "I could not minimize the window."


def maximize_window(app_name: str = None) -> str:
    """Maximize the foreground window or a named application window."""
    try:
        import win32gui
        import win32con

        if app_name:
            def _enum_cb(hwnd, results):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name.lower() in title and win32gui.IsWindowVisible(hwnd):
                    results.append(hwnd)

            results = []
            win32gui.EnumWindows(_enum_cb, results)
            if results:
                win32gui.ShowWindow(results[0], win32con.SW_MAXIMIZE)
                return f"Maximized {app_name}."
            return f"I could not find a window for {app_name}."
        else:
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return "Window maximized."
    except Exception as e:
        logger.error(f"maximize_window error: {e}")
        return "I could not maximize the window."


def close_window(app_name: str = None) -> str:
    """Close the foreground window or a named application window."""
    try:
        import win32gui
        import win32con

        if app_name:
            def _enum_cb(hwnd, results):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name.lower() in title and win32gui.IsWindowVisible(hwnd):
                    results.append(hwnd)

            results = []
            win32gui.EnumWindows(_enum_cb, results)
            if results:
                win32gui.PostMessage(results[0], win32con.WM_CLOSE, 0, 0)
                return f"Closing {app_name}."
            return f"I could not find a window for {app_name}."
        else:
            hwnd = win32gui.GetForegroundWindow()
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return "Window closed."
    except Exception as e:
        logger.error(f"close_window error: {e}")
        return "I could not close the window."


def lock_screen() -> str:
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Locking the screen."
    except Exception as e:
        logger.error(f"lock_screen error: {e}")
        return "I could not lock the screen."


def shutdown_system() -> str:
    try:
        subprocess.Popen(["shutdown", "/s", "/t", "30"])
        return "Shutting down your PC in 30 seconds. Say 'cancel shutdown' to abort."
    except Exception as e:
        logger.error(f"shutdown_system error: {e}")
        return "I could not initiate a shutdown."


def cancel_shutdown() -> str:
    try:
        subprocess.Popen(["shutdown", "/a"])
        return "Shutdown cancelled."
    except Exception as e:
        return "I could not cancel the shutdown."


def restart_system() -> str:
    try:
        subprocess.Popen(["shutdown", "/r", "/t", "30"])
        return "Restarting your PC in 30 seconds. Say 'cancel shutdown' to abort."
    except Exception as e:
        return "I could not initiate a restart."


def sleep_system() -> str:
    try:
        # Hibernate=False means sleep (S3), not hibernate
        ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
        return "Putting your PC to sleep."
    except Exception as e:
        logger.error(f"sleep_system error: {e}")
        # Fallback using rundll32
        try:
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Putting your PC to sleep."
        except Exception:
            return "I could not put your PC to sleep."


def minimize_all_windows() -> str:
    """Minimize all open windows using Win+D shortcut."""
    try:
        import win32api
        import win32con
        # Send Win+D to the desktop
        win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
        win32api.keybd_event(0x44, 0, 0, 0)   # 'D'
        win32api.keybd_event(0x44, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
        return "All windows minimized."
    except Exception as e:
        logger.error(f"minimize_all error: {e}")
        return "I could not minimize all windows."

def take_screenshot() -> str:
    try:
        from PIL import ImageGrab
        import time, os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        fname = f"screenshot_{int(time.time())}.png"
        path = os.path.join(desktop, fname)
        img = ImageGrab.grab()
        img.save(path)
        return f"Screenshot saved to your Desktop."
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return "I could not take a screenshot. Please ensure Pillow is installed."
