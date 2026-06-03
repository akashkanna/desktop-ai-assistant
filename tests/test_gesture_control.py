import pytest
from automation.gesture_control import GestureController as LegacyGestureController
from gesture import GestureController


def test_gesture_controller_api_exists():
    controller = GestureController()
    assert hasattr(controller, "start")
    assert hasattr(controller, "stop")
    assert hasattr(controller, "move_active_window_left")
    assert hasattr(controller, "move_active_window_right")
    assert hasattr(controller, "scroll_to_top")
    assert hasattr(controller, "scroll_to_bottom")
    assert hasattr(controller, "paused")
    assert controller.running is False
    assert GestureController is LegacyGestureController


def test_gesture_controller_start_stop_handles_missing_deps():
    controller = GestureController()
    try:
        import mediapipe  # type: ignore
        import cv2  # type: ignore
    except ImportError:
        result = controller.start()
        assert result == "Hand gesture control requires OpenCV and MediaPipe. Please install them first."
        return

    result = controller.start()
    assert "Hand gesture control" in result
    controller.stop()
