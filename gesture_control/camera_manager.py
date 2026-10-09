"""
Camera Manager module for Jarvis Gesture Control.
Handles asynchronous, thread-safe webcam access.
"""

import cv2
import threading
import time
from logger_config import setup_logger

logger = setup_logger("camera_manager")

class CameraManager:
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        
        self.cap = None
        self.latest_frame = None
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.running = False

    def start(self) -> bool:
        """Starts the asynchronous camera capture loop."""
        if self.running:
            return True
            
        logger.info(f"Opening camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera index {self.camera_index}")
            self.cap = None
            return False
            
        # Apply camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Verify applied settings
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Camera opened. Resolution set to {actual_w}x{actual_h}")
        
        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, name="CameraCaptureThread", daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stops the camera capture and releases resources."""
        if not self.running:
            return
            
        logger.info("Stopping camera manager...")
        self.running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=1.5)
            self._thread = None
            
        with self._lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.latest_frame = None
        logger.info("Camera manager stopped and camera released.")

    def get_frame(self):
        """Returns a copy of the latest frame in a thread-safe manner."""
        with self._lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None

    def _capture_loop(self):
        """Webcam capture loop running in a background thread."""
        fps_sleep = 1.0 / 30.0  # Cap at 30 FPS
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if ret:
                with self._lock:
                    self.latest_frame = frame
            else:
                logger.warning("Camera failed to read frame, retrying...")
                time.sleep(0.1)
                continue
                
            # Keep 30 FPS pacing
            elapsed = time.time() - start_time
            sleep_time = max(0.001, fps_sleep - elapsed)
            time.sleep(sleep_time)
            
        self.running = False
