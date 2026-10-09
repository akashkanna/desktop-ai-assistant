"""
Gesture Detector module for Jarvis Gesture Control.
Analyzes finger extension states and velocities to recognize static and dynamic controls.
"""

import math
import time
from collections import deque
from logger_config import setup_logger

logger = setup_logger("gesture_detector")

class GestureDetector:
    def __init__(self, history_len: int = 15):
        # Motion history buffers for up to 2 hands: hand_idx -> deque of (timestamp, x, y)
        self.motion_history = {0: deque(maxlen=history_len), 1: deque(maxlen=history_len)}
        self.last_swipe_time = 0.0

    def detect_gestures(self, hands, settings):
        """Classifies hand gestures from tracked hands and returns telemetry data."""
        if not hands:
            return {
                "gesture": "None",
                "confidence": 0.0,
                "hand_count": 0,
                "fingers": {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}
            }

        # --- MULTI-HAND GESTURES ---
        if len(hands) >= 2:
            h1_f = self._get_finger_extensions(hands[0]["landmarks"])
            h2_f = self._get_finger_extensions(hands[1]["landmarks"])
            
            # Both Hands Open -> Show Desktop
            if self._is_open_palm(h1_f, hands[0]["landmarks"]) and self._is_open_palm(h2_f, hands[1]["landmarks"]):
                return {
                    "gesture": "Both Hands Open",
                    "confidence": 0.98,
                    "hand_count": 2,
                    "fingers": h1_f,
                    "hand_label": "Both"
                }
            
            # Fallback to single-hand logic for the primary hand
            # but indicate 2 hands are present
            pass

        # --- SINGLE HAND GESTURES ---
        hand = hands[0]
        landmarks = hand["landmarks"]
        label = hand["label"]
        hand_confidence = hand.get("confidence", 0.85)
        
        # 1. Classify finger states
        fingers = self._get_finger_extensions(landmarks)
        
        # Register position in history buffer
        wrist = landmarks["WRIST"]
        hand_idx = 0
        self.motion_history[hand_idx].append((time.time(), wrist[0], wrist[1]))
        
        # 2. Closed Fist checks
        if self._is_closed_fist(fingers):
            # Fist Up / Fist Down dynamic swipes
            fist_swipe = self._detect_fist_swipe(hand_idx)
            if fist_swipe:
                return {
                    "gesture": fist_swipe,
                    "confidence": 0.90,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label
                }
            # Fist Hold
            return {
                "gesture": "Closed Fist",
                "confidence": 0.95,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # 3. Open Palm checks
        if self._is_open_palm(fingers, landmarks):
            # Dynamic horizontal swipes (Swipe Left / Swipe Right)
            swipe = self._detect_palm_swipe(hand_idx)
            if swipe:
                return {
                    "gesture": swipe,
                    "confidence": 0.92,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label
                }
            
            # Dynamic vertical movement -> Open Palm Scroll
            scroll = self._detect_scroll_motion(hand_idx)
            if scroll:
                return {
                    "gesture": "Open Palm Scroll",
                    "confidence": 0.88,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label
                }
                
            return {
                "gesture": "Open Palm",
                "confidence": 0.95,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # 4. Three Fingers Snapping Swipes (Index, Middle, Ring extended)
        if self._is_three_fingers(fingers):
            three_swipe = self._detect_three_finger_swipe(hand_idx)
            if three_swipe:
                return {
                    "gesture": three_swipe,
                    "confidence": 0.90,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label
                }
            return {
                "gesture": "Three Fingers",
                "confidence": 0.75,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # 5. Peace Sign Swipes (Alt-Tab)
        if self._is_peace_sign(fingers, landmarks):
            peace_swipe = self._detect_peace_swipe(hand_idx)
            if peace_swipe:
                return {
                    "gesture": "Peace Sign Swipe",
                    "confidence": 0.91,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label
                }
            return {
                "gesture": "Peace Sign",
                "confidence": 0.80,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # 6. Analogue Slider Control (Volume/Brightness)
        # Thumb & Index extended (Slider Volume)
        if fingers["thumb"] and fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            dist_val = self._dist(landmarks["THUMB_TIP"], landmarks["INDEX_FINGER_TIP"])
            if dist_val > settings.pinch_click_threshold * 1.5:  # ensure it's not a pinch
                return {
                    "gesture": "Thumb Index Slider",
                    "confidence": 0.92,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label,
                    "slider_value": dist_val
                }

        # Thumb & Middle extended (Slider Brightness)
        if fingers["thumb"] and fingers["middle"] and not fingers["index"] and not fingers["ring"] and not fingers["pinky"]:
            dist_val = self._dist(landmarks["THUMB_TIP"], landmarks["MIDDLE_FINGER_TIP"])
            if dist_val > settings.pinch_click_threshold * 1.5:
                return {
                    "gesture": "Thumb Middle Slider",
                    "confidence": 0.92,
                    "hand_count": 1,
                    "fingers": fingers,
                    "hand_label": label,
                    "slider_value": dist_val
                }

        # 7. Pinches (Left Click / Right Click)
        # Thumb + Middle Pinch -> Right Click
        if self._is_thumb_middle_pinch(landmarks, settings.pinch_click_threshold):
            return {
                "gesture": "Right Click",
                "confidence": 0.95,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # Thumb + Index Pinch -> Left Click
        if self._is_thumb_index_pinch(landmarks, settings.pinch_click_threshold):
            return {
                "gesture": "Left Click",
                "confidence": 0.96,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        # 8. Index extended -> Cursor Control
        if self._is_cursor_mode(fingers):
            return {
                "gesture": "Index Finger",
                "confidence": 0.97,
                "hand_count": 1,
                "fingers": fingers,
                "hand_label": label
            }

        return {
            "gesture": "Tracking",
            "confidence": 0.60,
            "hand_count": 1,
            "fingers": fingers,
            "hand_label": label
        }

    def _get_finger_extensions(self, landmarks):
        """Calculates rotation-invariant open/closed state of fingers."""
        wrist = landmarks["WRIST"]
        
        # Check if a finger is extended comparing Tip-to-Wrist vs PIP-to-Wrist
        def check_extended(finger_name):
            name_upper = finger_name.upper()
            tip = landmarks[f"{name_upper}_FINGER_TIP"] if finger_name != "pinky" else landmarks["PINKY_TIP"]
            pip = landmarks[f"{name_upper}_FINGER_PIP"] if finger_name != "pinky" else landmarks["PINKY_PIP"]
            return self._dist(tip, wrist) > self._dist(pip, wrist) * 1.05

        # Thumb extension sideways check
        thumb_tip = landmarks["THUMB_TIP"]
        thumb_ip = landmarks["THUMB_IP"]
        # Thumb is extended if the tip is far from wrist relative to IP joint
        thumb_extended = self._dist(thumb_tip, wrist) > self._dist(thumb_ip, wrist) * 1.03

        return {
            "thumb": thumb_extended,
            "index": check_extended("index"),
            "middle": check_extended("middle"),
            "ring": check_extended("ring"),
            "pinky": check_extended("pinky")
        }

    def _is_cursor_mode(self, fingers):
        return fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]

    def _is_closed_fist(self, fingers):
        return not fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]

    def _is_open_palm(self, fingers, landmarks):
        if not (fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]):
            return False
        # Add span verification
        index_tip = landmarks["INDEX_FINGER_TIP"]
        pinky_tip = landmarks["PINKY_TIP"]
        wrist = landmarks["WRIST"]
        hand_size = self._dist(wrist, landmarks["MIDDLE_FINGER_MCP"])
        return self._dist(index_tip, pinky_tip) > hand_size * 0.85

    def _is_two_finger_scroll(self, fingers):
        return fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]

    def _is_three_fingers(self, fingers):
        return fingers["index"] and fingers["middle"] and fingers["ring"] and not fingers["pinky"]

    def _is_peace_sign(self, fingers, landmarks):
        if not (fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]):
            return False
        # Index tip & Middle tip must be separated
        dist_tips = self._dist(landmarks["INDEX_FINGER_TIP"], landmarks["MIDDLE_FINGER_TIP"])
        hand_size = self._dist(landmarks["WRIST"], landmarks["MIDDLE_FINGER_MCP"])
        return dist_tips > hand_size * 0.30

    def _is_thumb_index_pinch(self, landmarks, threshold):
        thumb_tip = landmarks["THUMB_TIP"]
        index_tip = landmarks["INDEX_FINGER_TIP"]
        hand_size = self._dist(landmarks["WRIST"], landmarks["MIDDLE_FINGER_MCP"])
        return self._dist(thumb_tip, index_tip) < hand_size * threshold * 8.0

    def _is_thumb_middle_pinch(self, landmarks, threshold):
        thumb_tip = landmarks["THUMB_TIP"]
        middle_tip = landmarks["MIDDLE_FINGER_TIP"]
        hand_size = self._dist(landmarks["WRIST"], landmarks["MIDDLE_FINGER_MCP"])
        return self._dist(thumb_tip, middle_tip) < hand_size * threshold * 8.0

    # Dynamic motion velocity parsing helpers
    # ==========================================
    def _detect_palm_swipe(self, hand_idx):
        history = self.motion_history[hand_idx]
        if len(history) < 8:
            return None
        
        first = history[0]
        last = history[-1]
        dt = last[0] - first[0]
        
        if dt <= 0 or dt > 0.8:
            return None
            
        dx = last[1] - first[1]
        dy = last[2] - first[2]
        
        # Horizontal check
        if abs(dx) > 0.22 and abs(dx) > abs(dy) * 1.6:
            # Mirror corrections (mirrored webcam: moving left increases raw x)
            if dx > 0:
                return "Swipe Left"
            else:
                return "Swipe Right"
        return None

    def _detect_three_finger_swipe(self, hand_idx):
        history = self.motion_history[hand_idx]
        if len(history) < 8:
            return None
            
        first = history[0]
        last = history[-1]
        dt = last[0] - first[0]
        
        if dt <= 0 or dt > 0.8:
            return None
            
        dx = last[1] - first[1]
        dy = last[2] - first[2]
        
        if abs(dx) > 0.20 and abs(dx) > abs(dy) * 1.6:
            if dx > 0:
                return "Three Fingers Swipe Left"
            else:
                return "Three Fingers Swipe Right"
        return None

    def _detect_fist_swipe(self, hand_idx):
        history = self.motion_history[hand_idx]
        if len(history) < 8:
            return None
            
        first = history[0]
        last = history[-1]
        dt = last[0] - first[0]
        
        if dt <= 0 or dt > 0.8:
            return None
            
        dx = last[1] - first[1]
        dy = last[2] - first[2]
        
        # Vertical check
        if abs(dy) > 0.20 and abs(dy) > abs(dx) * 1.5:
            # Mirror correction: y coordinate decreases moving up
            if dy < 0:
                return "Fist Up"
            else:
                return "Fist Down"
        return None

    def _detect_peace_swipe(self, hand_idx):
        history = self.motion_history[hand_idx]
        if len(history) < 8:
            return None
            
        first = history[0]
        last = history[-1]
        dt = last[0] - first[0]
        
        if dt <= 0 or dt > 0.8:
            return None
            
        dx = last[1] - first[1]
        dy = last[2] - first[2]
        
        if abs(dx) > 0.18 and abs(dx) > abs(dy) * 1.5:
            return "Peace Sign Swipe"
        return None

    def _detect_scroll_motion(self, hand_idx):
        history = self.motion_history[hand_idx]
        if len(history) < 5:
            return False
            
        first = history[-4]
        last = history[-1]
        dy = abs(last[2] - first[2])
        dx = abs(last[1] - first[1])
        
        # If moving mostly vertically, mark as scrolling
        return dy > 0.03 and dy > dx * 1.3

    def _dist(self, p1, p2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
