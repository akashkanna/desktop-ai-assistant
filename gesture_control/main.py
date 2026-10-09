"""
Main Coordinator for Jarvis Gesture Control.
Orchestrates camera manager, hand tracker, detector, state machine, action executor,
and emits thread-safe PySide6 signals to drive UI overlays and dashboards.
"""

import time
import threading
from PySide6.QtCore import QObject, Signal, Slot
from logger_config import setup_logger

from gesture_control.settings import GestureSettings
from gesture_control.camera_manager import CameraManager
from gesture_control.hand_tracker import HandTracker
from gesture_control.gesture_detector import GestureDetector
from gesture_control.gesture_state_machine import GestureStateMachine, GestureState
from gesture_control.action_executor import ActionExecutor

logger = setup_logger("gesture_main")

class GestureManager(QObject):
    # Signals matching legacy GestureController interface
    frame_ready = Signal(object)  # Emits raw or drawn cv2 frame
    status_updated = Signal(bool, bool, bool, float)  # camera_connected, hand_detected, gesture_active, confidence
    gesture_detected = Signal(str, float, str, str)  # name, confidence, action_label, command
    camera_error = Signal(str)
    
    # Advanced telemetry signal for the Jarvis dashboard overlay
    telemetry_updated = Signal(object, dict)  # cv_frame, telemetry_dict

    def __init__(self):
        super().__init__()
        self.settings = GestureSettings()
        
        # Managers
        self.camera_mgr = None
        self.tracker = None
        self.detector = GestureDetector()
        self.state_machine = GestureStateMachine()
        self.executor = ActionExecutor()

        # Debug telemetry
        self.debug_status = {
            "camera_frame_received": False,
            "rgb_conversion": False,
            "hands_detected": 0,
            "left_hand": False,
            "right_hand": False,
            "detection_confidence": 0.0,
            "failure_reason": None,
        }
        
        # Operational flags
        self.running = False
        self.camera_enabled = False
        self.gesture_enabled = False
        self._thread = None
        self._stop_requested = threading.Event()
        self._action_callback = None
        
        # Telemetry fields
        self.fps = 0.0
        self.last_frame_time = time.time()

    @property
    def paused(self) -> bool:
        return self.state_machine.paused

    @paused.setter
    def paused(self, val: bool):
        self.state_machine.paused = val

    def set_action_callback(self, callback):
        """Sets callback to execute voice-equivalent text commands (e.g. 'activate jarvis')."""
        self._action_callback = callback

    def start(self) -> str:
        """Starts both camera and gesture control."""
        if self.camera_enabled and self.gesture_enabled:
            return "Hand gesture control is already running."
            
        cam_res = self.start_camera()
        if "failed" in cam_res.lower() or "error" in cam_res.lower():
            return cam_res
            
        gesture_res = self.start_gesture()
        if "failed" in gesture_res.lower() or "error" in gesture_res.lower():
            self.stop_camera()
            return gesture_res
            
        return (
            "Hand gesture control started. Use one finger to move the cursor, "
            "pinch for left click, two-finger pinch for right click, "
            "open palm to pause, and swipe left/right for browser navigation."
        )

    def stop(self) -> str:
        """Stops both camera and gesture control."""
        self.stop_gesture()
        self.stop_camera()
        return "Hand gesture control stopped."

    def start_camera(self) -> str:
        """Starts the camera acquisition."""
        if self.camera_enabled:
            return "Camera is already active."
            
        self.camera_mgr = CameraManager(
            camera_index=self.settings.camera_index,
            width=self.settings.camera_width,
            height=self.settings.camera_height
        )
        
        if not self.camera_mgr.start():
            self.camera_enabled = False
            self.camera_error.emit("Could not open webcam.")
            return "Hand gesture control failed to start: camera unavailable or initialization timed out."
            
        self.camera_enabled = True
        self._start_worker()
        return "Camera enabled and ready. Gesture support can be activated separately."

    def stop_camera(self) -> str:
        """Stops the camera manager."""
        if not self.camera_enabled:
            return "Camera is not active."
            
        self.camera_enabled = False
        self._check_and_stop_worker()
        
        if self.camera_mgr:
            self.camera_mgr.stop()
            self.camera_mgr = None
            
        self.status_updated.emit(False, False, self.gesture_enabled, 0.0)
        return "Camera stopped. Gesture mode is now disabled."

    def start_gesture(self) -> str:
        """Enables gesture classification and execution mapping."""
        if self.gesture_enabled:
            return "Gesture mode is already enabled."
            
        self.tracker = HandTracker(
            num_hands=self.settings.max_num_hands,
            smoothing_factor=self.settings.cursor_smoothing,
            min_detection_confidence=self.settings.min_detection_confidence,
            min_tracking_confidence=self.settings.min_tracking_confidence,
            model_complexity=self.settings.model_complexity,
            model_path=self.settings.model_path,
        )
        if not self.tracker.initialize_model():
            failure_reason = getattr(self.tracker, "last_debug", {}).get("failure_reason")
            self.tracker = None
            return (
                f"Hand gesture control could not enable gesture mode: "
                f"{failure_reason or 'MediaPipe initialization failed.'}"
            )
            
        self.gesture_enabled = True
        self._start_worker()
        return "Gesture mode enabled. Hand gestures are now active."

    def stop_gesture(self) -> str:
        """Disables gesture mapping without necessarily turning off the camera."""
        if not self.gesture_enabled:
            return "Gesture mode is not enabled."
            
        self.gesture_enabled = False
        self._check_and_stop_worker()
        
        if self.tracker:
            self.tracker.close()
            self.tracker = None
            
        self.status_updated.emit(self.camera_enabled, False, False, 0.0)
        return "Gesture mode stopped."

    def _start_worker(self):
        """Starts the background processing worker thread if it isn't running."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_requested.clear()
        self.running = True
        self._thread = threading.Thread(target=self._processing_loop, name="GestureProcessingThread", daemon=True)
        self._thread.start()
        logger.info("Gesture processing loop thread started.")

    def _check_and_stop_worker(self):
        """Stops the background worker thread if both inputs are off."""
        if not self.camera_enabled and not self.gesture_enabled:
            self.running = False
            self._stop_requested.set()
            if self._thread:
                self._thread.join(timeout=1.0)
                self._thread = None
            logger.info("Gesture processing loop thread stopped.")

    def _processing_loop(self):
        """Background loop: fetches frames, tracks hand landmarks, and executes controls."""
        last_frame_time = time.time()
        
        while not self._stop_requested.is_set():
            loop_start = time.time()
            
            frame = self.camera_mgr.get_frame() if self.camera_mgr else None
            if frame is None:
                time.sleep(0.01)
                continue
                
            # Compute FPS
            now = time.time()
            dt = now - last_frame_time
            last_frame_time = now
            self.fps = (1.0 / dt) if dt > 0 else 30.0
            
            telemetry = {
                "gesture": "None",
                "confidence": 0.0,
                "action": "None",
                "mode": "NO_HAND",
                "fps": self.fps,
                "hand_count": 0,
                "fingers": {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}
            }
            
            # 2. Hand tracking and skeleton overlay
            hands = None
            self.debug_status = {
                "camera_frame_received": frame is not None,
                "rgb_conversion": False,
                "hands_detected": 0,
                "left_hand": False,
                "right_hand": False,
                "detection_confidence": 0.0,
                "failure_reason": None,
            }

            if self.tracker and self.gesture_enabled:
                hands = self.tracker.process_frame(frame)
                tracker_debug = getattr(self.tracker, "last_debug", {})
                self.debug_status.update({
                    "rgb_conversion": tracker_debug.get("rgb_converted", False),
                    "hands_detected": tracker_debug.get("hands_detected_count", 0),
                    "left_hand": tracker_debug.get("left_hand_detected", False),
                    "right_hand": tracker_debug.get("right_hand_detected", False),
                    "detection_confidence": tracker_debug.get("detection_confidence", 0.0),
                    "failure_reason": tracker_debug.get("failure_reason"),
                })

            if hands:
                hand_count = len(hands)
                telemetry["hand_count"] = hand_count
                telemetry["detection_confidence"] = self.debug_status["detection_confidence"]
                telemetry["hand_labels"] = [hand["label"] for hand in hands]
                
                # Draw skeleton overlays for all detected hands
                from gesture_control.gesture_overlay import GestureVisualsHelper
                for hand in hands:
                    frame = GestureVisualsHelper.draw_skeleton(frame, hand)
                
                # Retrieve primary hand data
                primary_hand = hands[0]
                landmarks = primary_hand["landmarks"]
                fingers = self.detector._get_finger_extensions(landmarks)
                telemetry["fingers"] = fingers
                
                # 3. Detect raw pose/motion
                gesture_data = self.detector.detect_gestures(hands, self.settings)
                gesture_name = gesture_data.get("gesture", "None")
                confidence = gesture_data.get("confidence", 0.0)
                slider_val = gesture_data.get("slider_value", None)
                
                telemetry["gesture"] = gesture_name
                telemetry["confidence"] = confidence
                
                # 4. Feed to State Machine
                state, action_triggered = self.state_machine.update(
                    gesture_name, confidence, hand_count, self.settings
                )
                
                # Override mode string in UI if user paused the system
                if self.paused:
                    telemetry["mode"] = "PAUSED"
                else:
                    telemetry["mode"] = state

                # Reset scroll velocity when we leave scroll modes
                if state != GestureState.TRACKING or gesture_name != "Open Palm Scroll":
                    self.executor.reset_scroll_tracking()

                # 5. Execute mapped OS Controls (Only if NOT paused)
                action_text = "None"
                if not self.paused:
                    # Continuous movement mapping
                    if gesture_name == "Index Finger" and state == GestureState.TRACKING:
                        index_tip = landmarks["INDEX_FINGER_TIP"]
                        self.executor.move_cursor(index_tip, self.settings)
                        action_text = "Mouse Move"
                        
                    elif gesture_name == "Open Palm Scroll" and state == GestureState.TRACKING:
                        index_tip = landmarks["INDEX_FINGER_TIP"]
                        self.executor.execute_vertical_scroll(index_tip, self.settings)
                        action_text = "Scroll Page"
                        
                    elif state == GestureState.GESTURE_PENDING and self.state_machine.pinch_hold_start:
                        index_tip = landmarks["INDEX_FINGER_TIP"]
                        self.executor.move_cursor(index_tip, self.settings)
                        action_text = "Drag Moving"

                    # Map triggered shortcuts
                    if action_triggered:
                        action_text = self._execute_action(action_triggered, gesture_name, confidence, slider_val)
                else:
                    # In paused mode, only look for the toggle unpause action
                    if action_triggered == "Pause System Toggle":
                        action_text = self._execute_action(action_triggered, gesture_name, confidence, None)
                        
                telemetry["action"] = action_text
                
                self.status_updated.emit(True, True, self.gesture_enabled, confidence)
            else:
                self.status_updated.emit(self.camera_enabled, False, self.gesture_enabled, 0.0)
                telemetry["mode"] = GestureState.NO_HAND
                telemetry["failure_reason"] = self.debug_status["failure_reason"]

            # Emit frames and telemetry
            self.frame_ready.emit(frame)
            self.telemetry_updated.emit(frame, telemetry)
            
            # Target 30 FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0.005, 0.033 - elapsed)
            time.sleep(sleep_time)

    def _execute_action(self, action_name, gesture_name, confidence, slider_value) -> str:
        """Executes actual OS commands and triggers callbacks."""
        logger.info(f"Executing action: {action_name}")
        
        # 1. Map to OS commands
        if action_name == "Left Click":
            self.executor.execute_click("left")
        elif action_name == "Right Click":
            self.executor.execute_click("right")
        elif action_name == "Double Click":
            self.executor.execute_click("double")
        elif action_name == "Drag Start":
            self.executor.drag_start()
        elif action_name == "Drag End":
            self.executor.drag_end()
        elif action_name == "Swipe Left":
            self.executor.execute_browser_back()
        elif action_name == "Swipe Right":
            self.executor.execute_browser_forward()
        elif action_name == "Three Fingers Swipe Left":
            self.executor.execute_prev_desktop()
        elif action_name == "Three Fingers Swipe Right":
            self.executor.execute_next_desktop()
        elif action_name == "Task View":
            self.executor.execute_task_view()
        elif action_name == "Both Hands Open":
            self.executor.execute_show_desktop()
        elif action_name == "Fist Up":
            self.executor.execute_maximize_window()
        elif action_name == "Fist Down":
            self.executor.execute_minimize_window()
        elif action_name == "Peace Sign Swipe":
            self.executor.execute_alt_tab()
        elif action_name == "Thumb Index Slider" and slider_value is not None:
            self.executor.execute_volume_slide(slider_value)
            return f"Volume Set ({self.executor.last_volume}%)"
        elif action_name == "Thumb Middle Slider" and slider_value is not None:
            self.executor.execute_brightness_slide(slider_value)
            return f"Brightness Set ({self.executor.last_brightness}%)"
        elif action_name == "Pause System Toggle":
            state_label = "Paused" if self.paused else "Active"
            logger.info(f"Gesture System is now: {state_label}")
            return f"System {state_label}"

        # 2. Emit signal matching legacy event schema
        action_label = self._gesture_action_label(gesture_name)
        command_text = self._gesture_command(gesture_name)
        
        self.gesture_detected.emit(gesture_name, confidence, action_label, command_text)
        
        # 3. Trigger Voice Activation Callback if needed
        if action_name == "Jarvis Activation" and self._action_callback:
            try:
                self._action_callback(command_text)
            except Exception as e:
                logger.error(f"Failed to execute Jarvis Activation callback: {e}")
                
        return action_name

    def _gesture_action_label(self, gesture_name: str) -> str:
        return {
            "Open Palm": "Activate Jarvis",
            "Closed Fist": "Pause Gesture System",
            "Swipe Left": "Browser Back",
            "Swipe Right": "Browser Forward",
            "Three Fingers Swipe Left": "Previous Virtual Desktop",
            "Three Fingers Swipe Right": "Next Virtual Desktop",
        }.get(gesture_name, "Gesture Action")

    def _gesture_command(self, gesture_name: str) -> str:
        return {
            "Open Palm": "activate jarvis",
            "Closed Fist": "pause gestures",
            "Swipe Left": "browser back",
            "Swipe Right": "browser forward",
            "Three Fingers Swipe Left": "previous desktop",
            "Three Fingers Swipe Right": "next desktop",
        }.get(gesture_name, "")

    # ==========================================
    # COMPATIBILITY INTERFACE
    # ==========================================
    def scroll_to_top(self) -> str:
        return self.executor.reset_scroll_tracking() or "Scrolled to top."

    def scroll_to_bottom(self) -> str:
        return "Scrolled to bottom."

    def move_active_window_left(self) -> str:
        self.executor.execute_move_window_left_monitor()
        return "Moved active window left."

    def move_active_window_right(self) -> str:
        self.executor.execute_move_window_right_monitor()
        return "Moved active window right."
