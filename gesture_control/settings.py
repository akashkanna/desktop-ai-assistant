"""
Settings module for Jarvis Gesture Control.
Manages configuration parameters and persists them to JSON.
"""

import json
from pathlib import Path
from logger_config import setup_logger

logger = setup_logger("gesture_settings")

DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "gesture_settings.json"

class GestureSettings:
    def __init__(self, settings_path: Path = DEFAULT_SETTINGS_PATH):
        self.settings_path = settings_path
        
        # MediaPipe Settings
        self.static_image_mode = False
        self.max_num_hands = 2
        self.model_complexity = 1
        self.min_detection_confidence = 0.7
        self.min_tracking_confidence = 0.7
        self.model_path = str(Path(__file__).resolve().parents[1] / "gesture" / "hand_landmarker.task")
        
        # Camera Resolution
        self.camera_index = 0
        self.camera_width = 640
        self.camera_height = 480
        
        # Cursor control settings
        self.cursor_sensitivity = 2.0
        self.cursor_smoothing = 0.35  # Exponential smoothing factor
        self.edge_margin = 15          # Boundary buffer in pixels
        
        # Scroll settings
        self.scroll_sensitivity = 1.5
        self.scroll_smoothing = 0.25
        
        # Confidence and thresholds
        self.min_gesture_confidence = 0.70
        self.gesture_cooldown = 0.6    # Seconds between actions
        self.pinch_click_threshold = 0.045
        self.double_pinch_window = 0.50
        self.activation_hold_duration = 2.0
        self.pause_hold_duration = 2.0
        
        # Load from disk if file exists
        self.load()

    def load(self):
        """Loads settings from disk, creating default settings file if missing."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Apply settings with fallbacks
                self.static_image_mode = data.get("static_image_mode", self.static_image_mode)
                self.max_num_hands = data.get("max_num_hands", self.max_num_hands)
                self.model_complexity = data.get("model_complexity", self.model_complexity)
                self.min_detection_confidence = data.get("min_detection_confidence", self.min_detection_confidence)
                self.min_tracking_confidence = data.get("min_tracking_confidence", self.min_tracking_confidence)
                self.model_path = data.get("model_path", self.model_path)
                
                self.camera_index = data.get("camera_index", self.camera_index)
                self.camera_width = data.get("camera_width", self.camera_width)
                self.camera_height = data.get("camera_height", self.camera_height)
                self.cursor_sensitivity = data.get("cursor_sensitivity", self.cursor_sensitivity)
                self.cursor_smoothing = data.get("cursor_smoothing", self.cursor_smoothing)
                self.edge_margin = data.get("edge_margin", self.edge_margin)
                self.scroll_sensitivity = data.get("scroll_sensitivity", self.scroll_sensitivity)
                self.scroll_smoothing = data.get("scroll_smoothing", self.scroll_smoothing)
                self.min_gesture_confidence = data.get("min_gesture_confidence", self.min_gesture_confidence)
                self.gesture_cooldown = data.get("gesture_cooldown", self.gesture_cooldown)
                self.pinch_click_threshold = data.get("pinch_click_threshold", self.pinch_click_threshold)
                self.double_pinch_window = data.get("double_pinch_window", self.double_pinch_window)
                self.activation_hold_duration = data.get("activation_hold_duration", self.activation_hold_duration)
                self.pause_hold_duration = data.get("pause_hold_duration", self.pause_hold_duration)
                
                logger.info(f"Gesture settings loaded from {self.settings_path}")
            else:
                self.save()
        except Exception as e:
            logger.error(f"Failed to load gesture settings: {e}")

    def save(self):
        """Persists current settings to disk."""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "static_image_mode": self.static_image_mode,
                "max_num_hands": self.max_num_hands,
                "model_complexity": self.model_complexity,
                "min_detection_confidence": self.min_detection_confidence,
                "min_tracking_confidence": self.min_tracking_confidence,
                "model_path": self.model_path,
                "camera_index": self.camera_index,
                "camera_width": self.camera_width,
                "camera_height": self.camera_height,
                "cursor_sensitivity": self.cursor_sensitivity,
                "cursor_smoothing": self.cursor_smoothing,
                "edge_margin": self.edge_margin,
                "scroll_sensitivity": self.scroll_sensitivity,
                "scroll_smoothing": self.scroll_smoothing,
                "min_gesture_confidence": self.min_gesture_confidence,
                "gesture_cooldown": self.gesture_cooldown,
                "pinch_click_threshold": self.pinch_click_threshold,
                "double_pinch_window": self.double_pinch_window,
                "activation_hold_duration": self.activation_hold_duration,
                "pause_hold_duration": self.pause_hold_duration
            }
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Gesture settings saved to {self.settings_path}")
        except Exception as e:
            logger.error(f"Failed to save gesture settings: {e}")
