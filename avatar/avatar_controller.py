"""
avatar_controller.py
Manages avatar visual states and emits state-change signals.
States: idle, listening, thinking, speaking, executing, error
"""

import logging
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AvatarState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    EXECUTING = "executing"
    ERROR = "error"
    SUCCESS = "success"


# Visual config per state
AVATAR_CONFIG = {
    AvatarState.IDLE: {
        "color": "#4A9EFF",
        "pulse": False,
        "label": "Ready",
        "emoji": "😊",
        "ring_color": "#1a3a6b",
        "glow": False,
    },
    AvatarState.LISTENING: {
        "color": "#00D4AA",
        "pulse": True,
        "label": "Listening...",
        "emoji": "👂",
        "ring_color": "#00D4AA",
        "glow": True,
    },
    AvatarState.THINKING: {
        "color": "#FFB347",
        "pulse": True,
        "label": "Thinking...",
        "emoji": "🤔",
        "ring_color": "#FF8C00",
        "glow": True,
    },
    AvatarState.SPEAKING: {
        "color": "#9B59B6",
        "pulse": True,
        "label": "Speaking...",
        "emoji": "🗣️",
        "ring_color": "#9B59B6",
        "glow": True,
    },
    AvatarState.EXECUTING: {
        "color": "#3498DB",
        "pulse": True,
        "label": "Executing...",
        "emoji": "⚙️",
        "ring_color": "#3498DB",
        "glow": True,
    },
    AvatarState.ERROR: {
        "color": "#E74C3C",
        "pulse": False,
        "label": "Error",
        "emoji": "❌",
        "ring_color": "#E74C3C",
        "glow": False,
    },
    AvatarState.SUCCESS: {
        "color": "#2ECC71",
        "pulse": False,
        "label": "Done!",
        "emoji": "✅",
        "ring_color": "#2ECC71",
        "glow": True,
    },
}


class AvatarController:
    """Tracks avatar state and notifies UI via callback."""

    def __init__(self, on_state_change: Callable[[AvatarState, dict], None] = None):
        self._state = AvatarState.IDLE
        self._on_change = on_state_change or (lambda s, c: None)

    @property
    def state(self) -> AvatarState:
        return self._state

    @property
    def config(self) -> dict:
        return AVATAR_CONFIG[self._state]

    def set_state(self, state: AvatarState):
        if state != self._state:
            self._state = state
            config = AVATAR_CONFIG[state]
            logger.debug(f"Avatar → {state.value}")
            self._on_change(state, config)

    def idle(self):
        self.set_state(AvatarState.IDLE)

    def listening(self):
        self.set_state(AvatarState.LISTENING)

    def thinking(self):
        self.set_state(AvatarState.THINKING)

    def speaking(self):
        self.set_state(AvatarState.SPEAKING)

    def executing(self):
        self.set_state(AvatarState.EXECUTING)

    def error(self):
        self.set_state(AvatarState.ERROR)

    def success(self):
        self.set_state(AvatarState.SUCCESS)
