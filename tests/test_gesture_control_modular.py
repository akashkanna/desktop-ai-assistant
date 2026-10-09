"""
Unit tests for the modular Jarvis Gesture Control system.
"""

import pytest
import time
from unittest.mock import MagicMock
from gesture_control.settings import GestureSettings
from gesture_control.gesture_state_machine import GestureStateMachine, GestureState
from gesture_control.gesture_detector import GestureDetector

def test_gesture_settings_load_save(tmp_path):
    temp_settings_file = tmp_path / "gesture_settings_test.json"
    settings = GestureSettings(settings_path=temp_settings_file)
    
    assert settings.camera_index == 0
    assert settings.cursor_sensitivity == 2.0
    
    settings.cursor_sensitivity = 3.5
    settings.save()
    
    settings_new = GestureSettings(settings_path=temp_settings_file)
    assert settings_new.cursor_sensitivity == 3.5

def test_gesture_state_machine_transitions():
    state_machine = GestureStateMachine()
    settings = MagicMock()
    settings.min_gesture_confidence = 0.70
    settings.gesture_cooldown = 0.5
    settings.activation_hold_duration = 2.0
    settings.pause_hold_duration = 2.0
    settings.double_pinch_window = 0.5
    
    # 1. Start state is NO_HAND
    assert state_machine.current_state == GestureState.NO_HAND
    
    # 2. Hand detected -> HAND_DETECTED
    state, action = state_machine.update("Tracking", 0.50, 1, settings)
    assert state == GestureState.HAND_DETECTED
    
    # 3. Next update -> TRACKING
    state, action = state_machine.update("Tracking", 0.50, 1, settings)
    assert state == GestureState.TRACKING
    
    # 4. Swipe Left -> ACTION_EXECUTED
    state, action = state_machine.update("Swipe Left", 0.95, 1, settings)
    assert state == GestureState.ACTION_EXECUTED
    assert action == "Swipe Left"

def test_gesture_state_machine_clicks():
    state_machine = GestureStateMachine()
    settings = MagicMock()
    settings.min_gesture_confidence = 0.70
    settings.gesture_cooldown = 0.1
    settings.activation_hold_duration = 2.0
    settings.pause_hold_duration = 2.0
    settings.double_pinch_window = 0.5
    
    # Go to tracking state
    state_machine.update("Tracking", 0.50, 1, settings)
    state_machine.update("Tracking", 0.50, 1, settings)
    
    # Left click pinch starts -> GESTURE_PENDING
    state, action = state_machine.update("Left Click", 0.95, 1, settings)
    assert state == GestureState.GESTURE_PENDING
    assert action is None
    
    # Release left pinch -> Left Click triggered, state becomes ACTION_EXECUTED
    state, action = state_machine.update("Tracking", 0.50, 1, settings)
    assert state == GestureState.ACTION_EXECUTED
    assert action == "Left Click"

def test_detector_distance_math():
    detector = GestureDetector()
    p1 = (0.0, 0.0, 0.0)
    p2 = (3.0, 4.0, 0.0)
    assert detector._dist(p1, p2) == 5.0
