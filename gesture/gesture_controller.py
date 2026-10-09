"""
Gesture Controller — Adapter class mapping legacy interface to the new
modular gesture_control package.
"""

from PySide6.QtCore import QObject, Signal
from gesture_control import GestureManager

class GestureController(QObject):
    # Standard signals required by UI and controllers
    frame_ready = Signal(object)
    status_updated = Signal(bool, bool, bool, float)
    gesture_detected = Signal(str, float, str, str)
    camera_error = Signal(str)

    def __init__(self, camera_index: int = 0):
        super().__init__()
        # Instantiate the new modular gesture manager coordinator
        self._manager = GestureManager()
        self._manager.settings.camera_index = camera_index
        
        # Connect coordinator signals directly to adapter outputs
        self._manager.frame_ready.connect(self.frame_ready.emit)
        self._manager.status_updated.connect(self.status_updated.emit)
        self._manager.gesture_detected.connect(self.gesture_detected.emit)
        self._manager.camera_error.connect(self.camera_error.emit)

    # Properties
    # ==========================================
    @property
    def running(self) -> bool:
        return self._manager.running

    @running.setter
    def running(self, val: bool):
        self._manager.running = val

    @property
    def camera_enabled(self) -> bool:
        return self._manager.camera_enabled

    @camera_enabled.setter
    def camera_enabled(self, val: bool):
        self._manager.camera_enabled = val

    @property
    def gesture_enabled(self) -> bool:
        return self._manager.gesture_enabled

    @gesture_enabled.setter
    def gesture_enabled(self, val: bool):
        self._manager.gesture_enabled = val

    @property
    def paused(self) -> bool:
        return self._manager.paused

    @paused.setter
    def paused(self, val: bool):
        self._manager.paused = val

    @property
    def camera_index(self) -> int:
        return self._manager.settings.camera_index

    @camera_index.setter
    def camera_index(self, val: int):
        self._manager.settings.camera_index = val

    # Methods
    # ==========================================
    def start(self) -> str:
        return self._manager.start()

    def stop(self) -> str:
        return self._manager.stop()

    def start_camera(self) -> str:
        return self._manager.start_camera()

    def stop_camera(self) -> str:
        return self._manager.stop_camera()

    def start_gesture(self) -> str:
        return self._manager.start_gesture()

    def stop_gesture(self) -> str:
        return self._manager.stop_gesture()

    def set_action_callback(self, callback):
        self._manager.set_action_callback(callback)

    def move_active_window_left(self) -> str:
        return self._manager.move_active_window_left()

    def move_active_window_right(self) -> str:
        return self._manager.move_active_window_right()

    def scroll_to_top(self) -> str:
        return self._manager.scroll_to_top()

    def scroll_to_bottom(self) -> str:
        return self._manager.scroll_to_bottom()
