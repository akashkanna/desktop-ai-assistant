"""
Gesture State Machine module for Jarvis Gesture Control.
Governs the five explicit states: NO_HAND, HAND_DETECTED, TRACKING, GESTURE_PENDING, ACTION_EXECUTED.
Manages hold timers and transition constraints.
"""

import time
from logger_config import setup_logger

logger = setup_logger("gesture_state_machine")

class GestureState:
    NO_HAND = "NO_HAND"
    HAND_DETECTED = "HAND_DETECTED"
    TRACKING = "TRACKING"
    GESTURE_PENDING = "GESTURE_PENDING"
    ACTION_EXECUTED = "ACTION_EXECUTED"

class GestureStateMachine:
    def __init__(self):
        self.current_state = GestureState.NO_HAND
        self.last_state_change = time.time()
        
        # State timers for sustained holds
        self.open_palm_hold_start = None
        self.fist_hold_start = None
        self.pinch_hold_start = None
        
        # Click cooldowns & double click window tracker
        self.last_action_time = 0.0
        self.last_left_click_time = 0.0
        
        # Status flags
        self.paused = False
        self.dragging = False

    def update(self, detected_gesture, confidence, hand_count, settings):
        """Drives the state machine based on detection input and triggers actions."""
        now = time.time()
        
        # Post-Execution recovery: Reset ACTION_EXECUTED back to TRACKING at the start
        # of the next update call to allow a 1-frame persistence.
        if self.current_state == GestureState.ACTION_EXECUTED:
            if detected_gesture not in ("Thumb Index Slider", "Thumb Middle Slider", "Left Click"):
                self._transition_to(GestureState.TRACKING)
                
        cooldown_elapsed = now - self.last_action_time
        in_cooldown = cooldown_elapsed < settings.gesture_cooldown
        
        # 1. State: NO_HAND
        if hand_count == 0:
            if self.current_state != GestureState.NO_HAND:
                action_triggered = "Drag Release" if self.dragging else None
                self.dragging = False
                self.pinch_hold_start = None
                self._transition_to(GestureState.NO_HAND)
                return self.current_state, action_triggered
            return self.current_state, None

        # 2. Transition: NO_HAND -> HAND_DETECTED
        if self.current_state == GestureState.NO_HAND:
            self._transition_to(GestureState.HAND_DETECTED)
            return self.current_state, None

        # 3. Transition: HAND_DETECTED -> TRACKING
        if self.current_state == GestureState.HAND_DETECTED:
            self._transition_to(GestureState.TRACKING)

        action_triggered = None
        
        # 4. Process Gesture Holds (Temporal validation)
        # ---------------------------------------------
        # Open Palm hold checks (Task View, Wake Jarvis)
        if detected_gesture == "Open Palm" and confidence >= settings.min_gesture_confidence:
            if self.open_palm_hold_start is None:
                self.open_palm_hold_start = now
                self._transition_to(GestureState.GESTURE_PENDING)
            else:
                hold_duration = now - self.open_palm_hold_start
                # 2 Seconds -> Wake Jarvis
                if hold_duration >= settings.activation_hold_duration:
                    if not in_cooldown:
                        action_triggered = "Jarvis Activation"
                        self.last_action_time = now
                        self.open_palm_hold_start = None
                        self._transition_to(GestureState.ACTION_EXECUTED)
                # 1 Second -> Task View
                elif hold_duration >= 1.0:
                    if not in_cooldown and self.current_state == GestureState.GESTURE_PENDING:
                        action_triggered = "Task View"
                        self.last_action_time = now
                        self._transition_to(GestureState.ACTION_EXECUTED)
        else:
            self.open_palm_hold_start = None

        # Closed Fist hold checks (Pause Gesture System)
        if detected_gesture == "Closed Fist" and confidence >= settings.min_gesture_confidence:
            if self.fist_hold_start is None:
                self.fist_hold_start = now
                self._transition_to(GestureState.GESTURE_PENDING)
            else:
                hold_duration = now - self.fist_hold_start
                if hold_duration >= settings.pause_hold_duration:
                    if not in_cooldown:
                        self.paused = not self.paused
                        action_triggered = "Pause System Toggle"
                        self.last_action_time = now
                        self.fist_hold_start = None
                        self._transition_to(GestureState.ACTION_EXECUTED)
        else:
            self.fist_hold_start = None

        # Pinch holds (Drag & Drop)
        if detected_gesture == "Left Click" and confidence >= settings.min_gesture_confidence:
            if self.pinch_hold_start is None:
                self.pinch_hold_start = now
                self._transition_to(GestureState.GESTURE_PENDING)
            else:
                hold_duration = now - self.pinch_hold_start
                # If held for > 0.4 seconds, initiate Drag Start
                if hold_duration >= 0.40 and not self.dragging:
                    self.dragging = True
                    action_triggered = "Drag Start"
                    self._transition_to(GestureState.ACTION_EXECUTED)
        else:
            if self.pinch_hold_start is not None:
                # Released pinch
                self.pinch_hold_start = None
                
                if self.dragging:
                    self.dragging = False
                    action_triggered = "Drag End"
                    self._transition_to(GestureState.TRACKING)
                else:
                    # Regular left click or double click checks
                    if not in_cooldown:
                        if now - self.last_left_click_time <= settings.double_pinch_window:
                            action_triggered = "Double Click"
                            self.last_action_time = now
                        else:
                            action_triggered = "Left Click"
                            self.last_left_click_time = now
                    self._transition_to(GestureState.ACTION_EXECUTED)

        # 5. Process Swipes & Instant Actions
        # ---------------------------------------------
        if detected_gesture in (
            "Right Click", "Swipe Left", "Swipe Right", "Three Fingers Swipe Left",
            "Three Fingers Swipe Right", "Both Hands Open", "Fist Up", "Fist Down",
            "Peace Sign Swipe", "Thumb Index Slider", "Thumb Middle Slider"
        ) and confidence >= settings.min_gesture_confidence:
            # Sliders execute continuously, shortcuts require cooldown
            is_slider = "Slider" in detected_gesture
            if not in_cooldown or is_slider:
                action_triggered = detected_gesture
                if not is_slider:
                    self.last_action_time = now
                self._transition_to(GestureState.ACTION_EXECUTED)

        # If hand is in default states, resolve to TRACKING
        if self.current_state == GestureState.GESTURE_PENDING and detected_gesture not in ("Open Palm", "Closed Fist", "Left Click"):
            self._transition_to(GestureState.TRACKING)

        return self.current_state, action_triggered

    def _transition_to(self, new_state):
        if self.current_state != new_state:
            logger.debug(f"State transition: {self.current_state} -> {new_state}")
            self.current_state = new_state
            self.last_state_change = time.time()
