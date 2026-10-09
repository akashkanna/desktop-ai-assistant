"""
Hand Tracker module for Jarvis Gesture Control.
Uses MediaPipe Tasks API HandLandmarker for hand landmark detection.
Auto-downloads `hand_landmarker.task` if missing and falls back to classic
MediaPipe Solutions Hands when the Tasks API or model is unavailable.
"""

import cv2
import importlib
import math
from pathlib import Path
from logger_config import setup_logger

logger = setup_logger("hand_tracker")

DEFAULT_HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task"

# Hand landmark indices map
HAND_LANDMARK_MAP = {
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

# Reverse map: index -> name
LANDMARK_INDEX_TO_NAME = {v: k for k, v in HAND_LANDMARK_MAP.items()}


class HandTracker:
    """
    Hand tracking wrapper that supports both MediaPipe Tasks HandLandmarker and
    classic MediaPipe Solutions Hands when available.
    Applies Exponential Moving Average (EMA) smoothing to reduce jitter.
    """

    def __init__(
        self,
        num_hands: int = 2,
        smoothing_factor: float = 0.35,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1,
        model_path: str | None = None,
    ):
        self.num_hands = num_hands
        self.smoothing_factor = smoothing_factor  # 0 = max smooth, 1 = raw
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.model_path = model_path

        self.hands = None
        self.api_mode = None
        self._initialized = False
        self.last_debug = {
            "frame_received": False,
            "rgb_converted": False,
            "hands_detected_count": 0,
            "left_hand_detected": False,
            "right_hand_detected": False,
            "detection_confidence": 0.0,
            "failure_reason": None,
            "mediapipe_initialized": False,
            "landmarks_extracted": False,
            "model_path": self.model_path,
        }

        # Smoothing history: hand_idx -> {landmark_name: (x, y, z)}
        self.prev_landmarks = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize_model(self) -> bool:
        """
        Initialises MediaPipe HandLandmarker via the Tasks API and explicit model path.
        """
        hand_landmarker = None
        try:
            hand_landmarker = importlib.import_module("mediapipe.tasks.python.vision.hand_landmarker")
        except Exception:
            hand_landmarker = None

        if hand_landmarker is not None:
            if not self.model_path:
                self.last_debug["failure_reason"] = "No MediaPipe hand model path configured."
                logger.error(self.last_debug["failure_reason"])
                return False

            model_file = Path(self.model_path)
            if not model_file.exists():
                self.last_debug["failure_reason"] = f"MediaPipe hand model not found at: {model_file}."
                logger.warning(self.last_debug["failure_reason"])
                if not self._download_default_model(model_file):
                    return False

            try:
                logger.debug(
                    f"Initializing MediaPipe HandLandmarker: model_path={model_file}, "
                    f"num_hands={self.num_hands}, "
                    f"min_detection_confidence={self.min_detection_confidence}, "
                    f"min_tracking_confidence={self.min_tracking_confidence}"
                )
                options = hand_landmarker.HandLandmarkerOptions(
                    base_options=hand_landmarker._BaseOptions(model_asset_path=str(model_file)),
                    running_mode=hand_landmarker._RunningMode.IMAGE,
                    num_hands=self.num_hands,
                    min_hand_detection_confidence=self.min_detection_confidence,
                    min_hand_presence_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence,
                )
                self.hands = hand_landmarker.HandLandmarker.create_from_options(options)
                self.api_mode = "tasks"
                self._initialized = True
                self.last_debug["mediapipe_initialized"] = True
                self.last_debug["failure_reason"] = None
                logger.info("MediaPipe HandLandmarker initialized successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize MediaPipe HandLandmarker: {e}")
                self.last_debug["failure_reason"] = f"MediaPipe model initialization failed: {e}"
                self.last_debug["mediapipe_initialized"] = False
                self.api_mode = None
                # Fall through to try classic Solutions Hands if available.

        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            logger.debug(
                f"Falling back to MediaPipe Solutions Hands: num_hands={self.num_hands}, "
                f"model_complexity={self.model_complexity}, "
                f"min_detection_confidence={self.min_detection_confidence}, "
                f"min_tracking_confidence={self.min_tracking_confidence}"
            )
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.num_hands,
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self.api_mode = "solutions"
            self._initialized = True
            self.last_debug["mediapipe_initialized"] = True
            logger.info("MediaPipe Solutions Hands initialized successfully.")
            return True
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import MediaPipe Solutions API: {e}")
            self.last_debug["failure_reason"] = f"MediaPipe import failed: {e}"
            return False
        except Exception as e:
            logger.error(f"Failed to initialise MediaPipe Solutions Hands: {e}")
            self.last_debug["failure_reason"] = f"MediaPipe initialization failed: {e}"
            return False

    def _download_default_model(self, model_file: Path) -> bool:
        """Download the default MediaPipe hand landmarker model if it is missing."""
        try:
            model_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading MediaPipe hand_landmarker.task to %s", model_file)
            import urllib.request
            with urllib.request.urlopen(DEFAULT_HAND_MODEL_URL, timeout=30) as response:
                model_bytes = response.read()
            with open(model_file, "wb") as f:
                f.write(model_bytes)
            logger.info("Downloaded MediaPipe hand_landmarker.task successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to download MediaPipe hand model: {e}")
            self.last_debug["failure_reason"] = f"MediaPipe model download failed: {e}"
            return False

    def close(self):
        """Releases MediaPipe resources."""
        if self.hands:
            try:
                self.hands.close()
                logger.info("MediaPipe Hands closed.")
            except Exception as e:
                logger.error(f"Error closing MediaPipe Hands: {e}")
            finally:
                self.hands = None
                self._initialized = False

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_frame(self, frame_bgr):
        """
        Process a BGR frame and return a list of hand data dicts, or None.

        Each dict contains:
            landmarks  : {name: (x, y, z)} — normalised [0,1] coordinates
            label      : "Left" | "Right"  (mirror-corrected)
            confidence : float
            bbox       : (x, y, w, h) in pixels
        """
        self.last_debug = {
            "frame_received": False,
            "rgb_converted": False,
            "hands_detected_count": 0,
            "left_hand_detected": False,
            "right_hand_detected": False,
            "detection_confidence": 0.0,
            "failure_reason": None,
            "mediapipe_initialized": self._initialized,
            "landmarks_extracted": False,
        }

        if not self._initialized:
            if not self.initialize_model():
                self.last_debug["failure_reason"] = "MediaPipe initialization failed"
                return None

        if frame_bgr is None:
            self.last_debug["failure_reason"] = "No camera frame received"
            return None

        self.last_debug["frame_received"] = True

        try:
            h, w = frame_bgr.shape[:2]
            logger.debug("Camera frame received for hand tracking.")

            # MediaPipe requires RGB
            try:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                self.last_debug["rgb_converted"] = True
                logger.debug("BGR to RGB conversion succeeded.")
            except Exception as err:
                self.last_debug["failure_reason"] = f"RGB conversion failed: {err}"
                logger.error(self.last_debug["failure_reason"])
                return None

            frame_rgb.flags.writeable = False          # perf: avoid copy

            if self.api_mode == "tasks":
                from mediapipe.tasks.python.vision.core import image as mp_image
                mp_input = mp_image.Image(mp_image.ImageFormat.SRGB, frame_rgb)
                result = self.hands.detect(mp_input)
            else:
                result = self.hands.process(frame_rgb)

            frame_rgb.flags.writeable = True

            if result is None:
                self.prev_landmarks.clear()
                self.last_debug["failure_reason"] = "MediaPipe returned no result"
                logger.warning(self.last_debug["failure_reason"])
                return None

            if self.api_mode == "tasks":
                hand_results = result.hand_landmarks
                handedness = result.handedness
            else:
                hand_results = result.multi_hand_landmarks
                handedness = result.multi_handedness

            if not hand_results:
                self.prev_landmarks.clear()
                self.last_debug["failure_reason"] = "No hands detected by MediaPipe"
                logger.warning(self.last_debug["failure_reason"])
                return None

            processed_hands = []

            for idx, hand_landmarks in enumerate(hand_results):
                # ---- handedness + confidence ----
                label = "Unknown"
                confidence = 0.85

                if handedness and idx < len(handedness):
                    if self.api_mode == "tasks":
                        cls = handedness[idx][0]
                        label = "Left" if cls.category_name == "Right" else "Right"
                    else:
                        cls = handedness[idx].classification[0]
                        label = "Left" if cls.label == "Right" else "Right"
                    confidence = float(cls.score)

                if label == "Left":
                    self.last_debug["left_hand_detected"] = True
                if label == "Right":
                    self.last_debug["right_hand_detected"] = True
                self.last_debug["detection_confidence"] += confidence

                # ---- raw landmark dict ----
                raw_dict = {}
                xs, ys = [], []
                for name, lm_idx in HAND_LANDMARK_MAP.items():
                    if self.api_mode == "tasks":
                        lm = hand_landmarks[lm_idx]
                    else:
                        lm = hand_landmarks.landmark[lm_idx]
                    raw_dict[name] = (lm.x, lm.y, lm.z)
                    xs.append(lm.x)
                    ys.append(lm.y)

                # ---- EMA smoothing ----
                smoothed = self._smooth_landmarks(raw_dict, idx)

                # ---- bounding box ----
                margin = 0.05
                min_x = max(0.0, min(xs) - margin)
                max_x = min(1.0, max(xs) + margin)
                min_y = max(0.0, min(ys) - margin)
                max_y = min(1.0, max(ys) + margin)

                bbox = (
                    int(min_x * w),
                    int(min_y * h),
                    int((max_x - min_x) * w),
                    int((max_y - min_y) * h),
                )

                processed_hands.append({
                    "landmarks":  smoothed,
                    "label":      label,
                    "confidence": confidence,
                    "bbox":       bbox,
                    # Keep raw mediapipe object for overlay drawing
                    "_mp_landmarks": hand_landmarks,
                })

            hand_count = len(processed_hands)
            self.last_debug["hands_detected_count"] = hand_count
            self.last_debug["detection_confidence"] = (
                self.last_debug["detection_confidence"] / hand_count if hand_count else 0.0
            )
            self.last_debug["landmarks_extracted"] = True
            self.last_debug["failure_reason"] = None

            logger.debug(
                f"MediaPipe detected {hand_count} hand(s), left={self.last_debug['left_hand_detected']} "
                f"right={self.last_debug['right_hand_detected']} confidence={self.last_debug['detection_confidence']:.2f}"
            )

            return processed_hands if processed_hands else None

        except Exception as e:
            logger.error(f"HandTracker.process_frame error: {e}", exc_info=True)
            self.last_debug["failure_reason"] = f"Processing error: {e}"
            return None

    # ------------------------------------------------------------------
    # Smoothing
    # ------------------------------------------------------------------

    def _smooth_landmarks(self, raw: dict, hand_idx: int) -> dict:
        """
        Applies Exponential Moving Average per landmark.
        alpha=1  → pure raw (no smoothing)
        alpha=0  → frozen at first frame (max smoothing)
        """
        alpha = self.smoothing_factor

        if hand_idx not in self.prev_landmarks:
            self.prev_landmarks[hand_idx] = dict(raw)
            return dict(raw)

        prev = self.prev_landmarks[hand_idx]
        smoothed = {}

        for name, (rx, ry, rz) in raw.items():
            if name in prev:
                px, py, pz = prev[name]
                sx = alpha * rx + (1.0 - alpha) * px
                sy = alpha * ry + (1.0 - alpha) * py
                sz = alpha * rz + (1.0 - alpha) * pz
                smoothed[name] = (sx, sy, sz)
            else:
                smoothed[name] = (rx, ry, rz)

        self.prev_landmarks[hand_idx] = smoothed
        return smoothed
