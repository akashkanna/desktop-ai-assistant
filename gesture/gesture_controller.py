"""
Gesture Controller — MediaPipe hand gesture engine for desktop actions.
Supports one-finger cursor control, pinch clicks, swipe browser navigation,
and open-palm pause/resume behavior.
"""

import threading
import time
from collections import deque
from pathlib import Path
from threading import Event
from logger_config import setup_logger

logger = setup_logger("gesture_controller")

# Hand landmark indices (MediaPipe COCO Hand Landmarks)
HAND_LANDMARKS = {
    "WRIST": 0,
    "THUMB_CMC": 1,
    "THUMB_MCP": 2,
    "THUMB_IP": 3,
    "THUMB_TIP": 4,
    "INDEX_FINGER_MCP": 5,
    "INDEX_FINGER_PIP": 6,
    "INDEX_FINGER_DIP": 7,
    "INDEX_FINGER_TIP": 8,
    "MIDDLE_FINGER_MCP": 9,
    "MIDDLE_FINGER_PIP": 10,
    "MIDDLE_FINGER_DIP": 11,
    "MIDDLE_FINGER_TIP": 12,
    "RING_FINGER_MCP": 13,
    "RING_FINGER_PIP": 14,
    "RING_FINGER_DIP": 15,
    "RING_FINGER_TIP": 16,
    "PINKY_MCP": 17,
    "PINKY_PIP": 18,
    "PINKY_DIP": 19,
    "PINKY_TIP": 20,
}


class GestureController:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.running = False
        self.camera_enabled = False
        self.gesture_enabled = False
        self.paused = False
        self._thread = None
        self._stop_requested = False
        self._camera_ready = Event()
        self._last_positions = deque(maxlen=12)
        self._last_click_time = 0.0
        self._last_navigation_time = 0.0
        self._last_gesture_time = 0.0
        self._debounce_seconds = 0.75
        self._pinch_threshold = 0.08
        self._swipe_min_distance = 0.24
        self._screen_width, self._screen_height = self._get_screen_size()
        self._imports_ready = False
        self._cv2 = None
        self._hand_landmarker = None
        self._mp_image = None
        self._init_error = None  # Store initialization errors
        self._camera = None

    def _get_screen_size(self):
        try:
            import pyautogui
            size = pyautogui.size()
            return size.width, size.height
        except Exception:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            except Exception:
                return 1920, 1080

    def _import_dependencies(self):
        if self._imports_ready:
            return
        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            self._cv2 = cv2
            self._mp = mp
            self._python_vision = vision
            self._imports_ready = True
        except ImportError as e:
            message = "OpenCV and MediaPipe are required for gesture control."
            logger.error(f"{message} Missing dependency: {e}")
            self._imports_ready = False
            raise ImportError(message) from e
        except Exception as e:
            logger.error(f"GestureController dependency load failed: {e}")
            self._imports_ready = False
            raise

    def start(self) -> str:
        if self.gesture_enabled and self.camera_enabled:
            return "Hand gesture control is already running."
        try:
            self._import_dependencies()
        except ImportError:
            return "Hand gesture control requires OpenCV and MediaPipe. Please install them first."
        except Exception as e:
            return f"Hand gesture control initialization error: {e}"
        self._stop_requested = False
        self._init_error = None
        self.gesture_enabled = True
        self.camera_enabled = True
        self._start_worker()
        initialized = self._camera_ready.wait(timeout=3.0)
        if not initialized or self._init_error:
            self.gesture_enabled = False
            return f"Hand gesture control failed to start: {self._init_error or 'camera unavailable or initialization timed out.'}"
        return (
            "Hand gesture control started. Use one finger to move the cursor, "
            "pinch for left click, two-finger pinch for right click, "
            "open palm to pause, and swipe left/right for browser navigation."
        )

    def stop(self) -> str:
        if not self.gesture_enabled and not self.camera_enabled:
            return "Hand gesture control is not currently running."
        self.gesture_enabled = False
        self.camera_enabled = False
        self._stop_requested = True
        if self._thread:
            self._thread.join(timeout=2.0)
        self._cleanup_camera()
        self._camera_ready.clear()
        self.running = False
        self.paused = False
        self._last_positions.clear()
        return "Hand gesture control stopped."

    def start_camera(self) -> str:
        if self.camera_enabled:
            return "Camera is already active."
        try:
            self._import_dependencies()
        except ImportError:
            return "Camera mode requires OpenCV and MediaPipe. Please install them first."
        except Exception as e:
            return f"Camera initialization error: {e}"
        self.camera_enabled = True
        self._stop_requested = False
        self._init_error = None
        self._start_worker()
        if not self._camera_ready.wait(timeout=3.0):
            return f"Hand gesture control could not activate the camera: {self._init_error or 'camera unavailable or initialization timed out.'}"
        return "Camera enabled and ready. Gesture support can be activated separately."

    def stop_camera(self) -> str:
        if not self.camera_enabled:
            return "Camera is not active."
        self.camera_enabled = False
        self._stop_requested = True
        if not self.gesture_enabled:
            self._camera_ready.clear()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._cleanup_camera()
        self.running = False
        self.paused = False
        return "Camera stopped. Gesture mode is now disabled."

    def start_gesture(self) -> str:
        if self.gesture_enabled:
            return "Gesture mode is already enabled."
        try:
            self._import_dependencies()
        except ImportError:
            return "Gesture mode requires OpenCV and MediaPipe. Please install them first."
        except Exception as e:
            return f"Gesture initialization error: {e}"
        self.gesture_enabled = True
        self.camera_enabled = True
        self._stop_requested = False
        self._init_error = None
        self._start_worker()
        if not self._camera_ready.wait(timeout=3.0):
            self.gesture_enabled = False
            return f"Hand gesture control could not enable gesture mode: {self._init_error or 'camera unavailable or initialization timed out.'}"
        return "Gesture mode enabled. Hand gestures are now active."

    def stop_gesture(self) -> str:
        if not self.gesture_enabled:
            return "Gesture mode is not enabled."
        self.gesture_enabled = False
        self._stop_requested = not self.camera_enabled
        if self._thread:
            self._thread.join(timeout=2.0)
        self.paused = False
        return "Gesture mode stopped."

    def _start_worker(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._camera_ready.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _cleanup_camera(self) -> None:
        if self._camera is not None:
            try:
                self._camera.release()
            except Exception:
                pass
            self._camera = None

    def _run(self):
        try:
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import HandLandmarkerOptions
            
            # Download model using MediaPipe utility if needed
            model_path = self._download_model()
            
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                num_hands=1
            )
            self._hand_landmarker = self._python_vision.HandLandmarker.create_from_options(options)
            logger.info("MediaPipe HandLandmarker initialized successfully.")
        except FileNotFoundError as e:
            error_msg = (
                "Hand gesture model file not found. The model will be downloaded automatically "
                "on first camera access. Please ensure you have internet connection."
            )
            logger.warning(error_msg)
            self._init_error = None  # Allow graceful degradation
            # Continue anyway - will try to load model on next attempt
            self._camera_ready.set()
        except Exception as e:
            error_msg = f"Failed to initialize MediaPipe Hand Landmarker: {str(e)}"
            logger.error(error_msg)
            self._init_error = error_msg
            self.running = False
            self._camera_ready.set()
            return

        try:
            cap = self._cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                error_msg = f"Could not open camera at index {self.camera_index}. Check if camera is connected and not in use by another application."
                logger.error(error_msg)
                self._init_error = error_msg
                self.running = False
                self._camera_ready.set()
                return
            self._camera = cap
            logger.info("Camera opened successfully.")
        except Exception as e:
            error_msg = f"Camera access error: {str(e)}"
            logger.error(error_msg)
            self._init_error = error_msg
            self.running = False
            self._camera_ready.set()
            return

        self.running = True  # Mark as running after successful initialization
        self._camera_ready.set()
        
        while not self._stop_requested:
            try:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera, retrying...")
                    time.sleep(0.1)
                    continue

                # Skip hand detection if landmarker failed to initialize
                if not self._hand_landmarker:
                    self._last_positions.clear()
                    time.sleep(0.02)
                    continue

                # Convert frame to RGB
                frame_rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
                h, w, c = frame_rgb.shape
                
                # Convert to MediaPipe Image
                mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame_rgb)
                
                # Detect hand landmarks
                detection_result = self._hand_landmarker.detect(mp_image)
                
                if detection_result and detection_result.hand_landmarks:
                    landmarks = detection_result.hand_landmarks[0]
                    # Convert landmarks to normalized coordinates for gesture processing
                    normalized_landmarks = self._normalize_landmarks(landmarks, h, w)
                    self._register_position(normalized_landmarks)
                    self._process_hand(normalized_landmarks)
                else:
                    self._last_positions.clear()
            except Exception as e:
                logger.error(f"Hand detection error: {e}")
                self._last_positions.clear()

            time.sleep(0.02)

        self._cleanup_camera()
        if self._hand_landmarker:
            try:
                self._hand_landmarker.close()
            except:
                pass
        self.running = False

    def _download_model(self):
        """Download hand landmarker model if not present."""
        gesture_dir = Path(__file__).parent
        model_path = gesture_dir / 'hand_landmarker.task'
        
        if model_path.exists():
            logger.info(f"Using cached model: {model_path}")
            return str(model_path)
        
        logger.info("Hand landmarker model not found locally, attempting download...")
        
        # Try to download using requests library (more flexible than urllib)
        try:
            import requests
            url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker.task'
            logger.info(f"Downloading from {url}...")
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                with open(model_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Model downloaded successfully to {model_path}")
                return str(model_path)
        except Exception as e:
            logger.debug(f"Download with requests failed: {e}")
        
        # Fallback: try urllib without timeout
        try:
            import urllib.request
            url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker.task'
            logger.info(f"Trying alternative download from {url}...")
            urllib.request.urlretrieve(url, str(model_path))
            logger.info(f"Model downloaded successfully to {model_path}")
            return str(model_path)
        except Exception as e:
            logger.debug(f"Alternative download failed: {e}")
        
        # If all download attempts fail, return model name and hope MediaPipe has it cached
        logger.warning("Could not download model - MediaPipe will attempt to use built-in model")
        return "hand_landmarker.task"

    def _normalize_landmarks(self, landmarks, h, w):
        """Convert MediaPipe landmarks to normalized format for gesture processing."""
        class NormalizedLandmarks:
            def __init__(self):
                self.landmark = [type('obj', (object,), {'x': 0, 'y': 0}) for _ in range(21)]
        
        normalized = NormalizedLandmarks()
        for i, landmark in enumerate(landmarks):
            # MediaPipe returns normalized coordinates (0-1)
            normalized.landmark[i].x = landmark.x
            normalized.landmark[i].y = landmark.y
        
        return normalized

    def _register_position(self, landmarks) -> None:
        index_tip = landmarks.landmark[HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        self._last_positions.append((time.time(), index_tip.x, index_tip.y))

    def _process_hand(self, landmarks) -> None:
        if self._is_open_palm(landmarks):
            if not self.paused:
                logger.info("Open palm detected. Pausing gesture actions.")
            self.paused = True
            self._last_positions.clear()
            return

        if self.paused:
            logger.info("Gesture actions resumed.")
        self.paused = False

        if self._is_thumb_index_pinch(landmarks):
            self._perform_click("left")
            self._last_positions.clear()
            return

        if self._is_index_middle_pinch(landmarks):
            self._perform_click("right")
            self._last_positions.clear()
            return

        if self._finger_extended(
            landmarks,
            HAND_LANDMARKS["INDEX_FINGER_TIP"],
            HAND_LANDMARKS["INDEX_FINGER_PIP"],
        ):
            self._move_cursor(landmarks)

        self._detect_swipe()

    def _perform_click(self, button: str = "left") -> None:
        now = time.time()
        if now - self._last_click_time < self._debounce_seconds:
            return
        self._last_click_time = now

        try:
            import pyautogui
            pyautogui.click(button=button)
            logger.info(f"Performed {button} click.")
            return
        except Exception:
            try:
                import win32api
                import win32con
                if button == "left":
                    down = win32con.MOUSEEVENTF_LEFTDOWN
                    up = win32con.MOUSEEVENTF_LEFTUP
                else:
                    down = win32con.MOUSEEVENTF_RIGHTDOWN
                    up = win32con.MOUSEEVENTF_RIGHTUP
                win32api.mouse_event(down, 0, 0, 0, 0)
                win32api.mouse_event(up, 0, 0, 0, 0)
                logger.info(f"Performed {button} click (win32 fallback).")
                return
            except Exception as e:
                logger.error(f"Click failed: {e}")

    def _move_cursor(self, landmarks) -> None:
        index_tip = landmarks.landmark[HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        screen_x = int(max(0, min(self._screen_width - 1, index_tip.x * self._screen_width)))
        screen_y = int(max(0, min(self._screen_height - 1, index_tip.y * self._screen_height)))
        try:
            import pyautogui
            pyautogui.moveTo(screen_x, screen_y, duration=0.05)
            logger.info("Moved cursor using one-finger tracking.")
        except Exception as e:
            logger.error(f"Cursor movement failed: {e}")

    def _detect_swipe(self) -> None:
        if len(self._last_positions) < 8:
            return

        first_time, first_x, first_y = self._last_positions[0]
        last_time, last_x, last_y = self._last_positions[-1]
        duration = last_time - first_time
        if duration <= 0 or duration > 1.0:
            return

        dx = last_x - first_x
        dy = last_y - first_y
        if abs(dx) < abs(dy) or abs(dx) < self._swipe_min_distance:
            return

        if time.time() - self._last_navigation_time < self._debounce_seconds:
            return

        if dx > 0:
            self._navigate_forward()
        else:
            self._navigate_back()

        self._last_navigation_time = time.time()
        self._last_positions.clear()

    def _navigate_back(self) -> None:
        try:
            import pyautogui
            pyautogui.hotkey("alt", "left")
            logger.info("Browser navigation: back.")
        except Exception:
            try:
                import win32api
                import win32con
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_LEFT, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_LEFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                logger.info("Browser navigation: back (win32 fallback).")
            except Exception as e:
                logger.error(f"Browser back navigation failed: {e}")

    def _navigate_forward(self) -> None:
        try:
            import pyautogui
            pyautogui.hotkey("alt", "right")
            logger.info("Browser navigation: forward.")
        except Exception:
            try:
                import win32api
                import win32con
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                logger.info("Browser navigation: forward (win32 fallback).")
            except Exception as e:
                logger.error(f"Browser forward navigation failed: {e}")

    def _hand_size(self, landmarks) -> float:
        wrist = landmarks.landmark[HAND_LANDMARKS["WRIST"]]
        middle_mcp = landmarks.landmark[HAND_LANDMARKS["MIDDLE_FINGER_MCP"]]
        return self._distance(wrist, middle_mcp)

    def _distance(self, p1, p2) -> float:
        return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5

    def _finger_extended(self, landmarks, tip_idx, pip_idx) -> bool:
        tip = landmarks.landmark[tip_idx]
        pip = landmarks.landmark[pip_idx]
        wrist = landmarks.landmark[HAND_LANDMARKS["WRIST"]]
        return self._distance(tip, wrist) > self._distance(pip, wrist) * 1.05

    def _is_open_palm(self, landmarks) -> bool:
        extended = 0
        extended += 1 if self._finger_extended(landmarks, HAND_LANDMARKS["INDEX_FINGER_TIP"], HAND_LANDMARKS["INDEX_FINGER_PIP"]) else 0
        extended += 1 if self._finger_extended(landmarks, HAND_LANDMARKS["MIDDLE_FINGER_TIP"], HAND_LANDMARKS["MIDDLE_FINGER_PIP"]) else 0
        extended += 1 if self._finger_extended(landmarks, HAND_LANDMARKS["RING_FINGER_TIP"], HAND_LANDMARKS["RING_FINGER_PIP"]) else 0
        extended += 1 if self._finger_extended(landmarks, HAND_LANDMARKS["PINKY_TIP"], HAND_LANDMARKS["PINKY_PIP"]) else 0
        if extended < 4:
            return False
        index_tip = landmarks.landmark[HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        pinky_tip = landmarks.landmark[HAND_LANDMARKS["PINKY_TIP"]]
        return self._distance(index_tip, pinky_tip) > self._hand_size(landmarks) * 1.1

    def _is_pointing(self, landmarks) -> bool:
        index_extended = self._finger_extended(landmarks, HAND_LANDMARKS["INDEX_FINGER_TIP"], HAND_LANDMARKS["INDEX_FINGER_PIP"])
        middle_extended = self._finger_extended(landmarks, HAND_LANDMARKS["MIDDLE_FINGER_TIP"], HAND_LANDMARKS["MIDDLE_FINGER_PIP"])
        ring_extended = self._finger_extended(landmarks, HAND_LANDMARKS["RING_FINGER_TIP"], HAND_LANDMARKS["RING_FINGER_PIP"])
        pinky_extended = self._finger_extended(landmarks, HAND_LANDMARKS["PINKY_TIP"], HAND_LANDMARKS["PINKY_PIP"])
        return index_extended and not (middle_extended or ring_extended or pinky_extended)

    def _is_thumb_index_pinch(self, landmarks) -> bool:
        thumb_tip = landmarks.landmark[HAND_LANDMARKS["THUMB_TIP"]]
        index_tip = landmarks.landmark[HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        return self._distance(thumb_tip, index_tip) < self._hand_size(landmarks) * self._pinch_threshold

    def _is_index_middle_pinch(self, landmarks) -> bool:
        index_tip = landmarks.landmark[HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        middle_tip = landmarks.landmark[HAND_LANDMARKS["MIDDLE_FINGER_TIP"]]
        ring_extended = self._finger_extended(landmarks, HAND_LANDMARKS["RING_FINGER_TIP"], HAND_LANDMARKS["RING_FINGER_PIP"])
        pinky_extended = self._finger_extended(landmarks, HAND_LANDMARKS["PINKY_TIP"], HAND_LANDMARKS["PINKY_PIP"])
        return (
            self._distance(index_tip, middle_tip) < self._hand_size(landmarks) * self._pinch_threshold
            and not ring_extended
            and not pinky_extended
        )

    def _get_active_window(self):
        try:
            import pygetwindow as gw
            return gw.getActiveWindow()
        except Exception:
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                return hwnd
            except Exception as e:
                logger.error(f"Active window retrieval failed: {e}")
                return None

    def _move_window_to_rect(self, hwnd_or_window, rect):
        try:
            if hasattr(hwnd_or_window, "moveTo"):
                hwnd_or_window.moveTo(rect[0], rect[1])
                hwnd_or_window.resizeTo(rect[2] - rect[0], rect[3] - rect[1])
                return True

            import win32gui
            if isinstance(hwnd_or_window, int):
                win32gui.MoveWindow(hwnd_or_window, rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], True)
                return True
        except Exception as e:
            logger.error(f"Window move failed: {e}")
        return False

    def _get_monitors(self):
        monitors = []
        try:
            from screeninfo import get_monitors
            for m in get_monitors():
                monitors.append((m.x, m.y, m.x + m.width, m.y + m.height))
        except Exception:
            try:
                import win32api
                monitor_info = win32api.EnumDisplayMonitors()
                for monitor in monitor_info:
                    hMonitor = monitor[0]
                    info = win32api.GetMonitorInfo(hMonitor)
                    monitors.append(tuple(info["Monitor"]))
            except Exception:
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    monitors.append((0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)))
                except Exception as e:
                    logger.error(f"Monitor detection failed: {e}")
        return sorted(monitors, key=lambda m: m[0])

    def _find_monitor_for_window(self, window_rect, monitors):
        wx = (window_rect[0] + window_rect[2]) / 2
        for monitor in monitors:
            if monitor[0] <= wx <= monitor[2]:
                return monitor
        return monitors[0] if monitors else None

    def _get_window_rect(self, hwnd_or_window):
        try:
            if hasattr(hwnd_or_window, "box"):
                box = hwnd_or_window.box
                return (box.left, box.top, box.left + box.width, box.top + box.height)
            if hasattr(hwnd_or_window, "left"):
                return (hwnd_or_window.left, hwnd_or_window.top, hwnd_or_window.left + hwnd_or_window.width, hwnd_or_window.top + hwnd_or_window.height)
            import win32gui
            rect = win32gui.GetWindowRect(hwnd_or_window)
            return rect
        except Exception as e:
            logger.error(f"Could not get window rect: {e}")
            return None

    def move_active_window_left(self) -> str:
        window = self._get_active_window()
        if window is None:
            return "I could not identify the active window."

        rect = self._get_window_rect(window)
        if not rect:
            return "Could not read active window bounds."

        monitors = self._get_monitors()
        if len(monitors) < 2:
            return "Multiple monitors were not detected."

        current_monitor = self._find_monitor_for_window(rect, monitors)
        if not current_monitor:
            return "Could not determine the current monitor."

        current_index = monitors.index(current_monitor)
        if current_index == 0:
            return "The active window is already on the leftmost monitor."

        target_monitor = monitors[current_index - 1]
        return self._move_window_to_monitor(window, rect, target_monitor)

    def move_active_window_right(self) -> str:
        window = self._get_active_window()
        if window is None:
            return "I could not identify the active window."

        rect = self._get_window_rect(window)
        if not rect:
            return "Could not read active window bounds."

        monitors = self._get_monitors()
        if len(monitors) < 2:
            return "Multiple monitors were not detected."

        current_monitor = self._find_monitor_for_window(rect, monitors)
        if not current_monitor:
            return "Could not determine the current monitor."

        current_index = monitors.index(current_monitor)
        if current_index == len(monitors) - 1:
            return "The active window is already on the rightmost monitor."

        target_monitor = monitors[current_index + 1]
        return self._move_window_to_monitor(window, rect, target_monitor)

    def _move_window_to_monitor(self, window, window_rect, target_monitor):
        width = window_rect[2] - window_rect[0]
        height = window_rect[3] - window_rect[1]
        target_x = target_monitor[0] + 50
        target_y = target_monitor[1] + 50
        target_rect = (target_x, target_y, target_x + width, target_y + height)
        if self._move_window_to_rect(window, target_rect):
            return f"Moved the active window to monitor at {target_monitor[0]}."
        return "The window could not be moved to the target monitor."

    def scroll_to_top(self) -> str:
        try:
            import pyautogui
            pyautogui.press("home")
            return "Scrolled to the top of the page."
        except Exception:
            try:
                import win32api
                import win32con
                win32api.keybd_event(win32con.VK_HOME, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_HOME, 0, win32con.KEYEVENTF_KEYUP, 0)
                return "Scrolled to the top of the page."
            except Exception as e:
                logger.error(f"scroll_to_top failed: {e}")
                return "I could not scroll to the top."

    def scroll_to_bottom(self) -> str:
        try:
            import pyautogui
            pyautogui.press("end")
            return "Scrolled to the bottom of the page."
        except Exception:
            try:
                import win32api
                import win32con
                win32api.keybd_event(win32con.VK_END, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_END, 0, win32con.KEYEVENTF_KEYUP, 0)
                return "Scrolled to the bottom of the page."
            except Exception as e:
                logger.error(f"scroll_to_bottom failed: {e}")
                return "I could not scroll to the bottom."
