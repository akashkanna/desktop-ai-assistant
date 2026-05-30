"""
Short-term (in-session) memory store.
Keeps recent commands, context state, and entity references in RAM.
"""
import time
from collections import deque
from typing import Any, Optional
from logger_config import setup_logger

logger = setup_logger("short_term_memory")

class ShortTermMemory:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self._history: deque = deque(maxlen=max_items)

        # Active context slots
        self.last_intent: Optional[str] = None
        self.last_app: Optional[str] = None
        self.last_website: Optional[str] = None
        self.last_contact: Optional[str] = None
        self.last_message: Optional[str] = None
        self.last_command_text: Optional[str] = None
        self.current_goal: Optional[str] = None
        self.pending_confirmation: Optional[dict] = None
        self.clarification_state: Optional[dict] = None
        self.is_awaiting_response: bool = False

    # ------------------------------------------------------------------ #
    # History
    # ------------------------------------------------------------------ #
    def add_to_history(self, role: str, text: str, intent: Optional[str] = None):
        """Add a conversation turn to history."""
        entry = {
            "role": role,        # "user" | "assistant"
            "text": text,
            "intent": intent,
            "timestamp": time.time()
        }
        self._history.append(entry)
        logger.debug(f"History [{role}]: {text[:80]}")

    def get_history(self, n: int = 10) -> list:
        """Return last n history items."""
        return list(self._history)[-n:]

    def get_history_text(self, n: int = 10) -> str:
        """Return readable summary of last n turns."""
        items = self.get_history(n)
        lines = []
        for item in items:
            ts = time.strftime("%H:%M:%S", time.localtime(item["timestamp"]))
            lines.append(f"[{ts}] {item['role'].upper()}: {item['text']}")
        return "\n".join(lines)

    def clear_history(self):
        self._history.clear()
        logger.info("Short-term history cleared.")

    # ------------------------------------------------------------------ #
    # Context slot updates
    # ------------------------------------------------------------------ #
    def update_context(self, **kwargs):
        """Update named context slots dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Context updated: {key} = {value}")
            else:
                logger.warning(f"Unknown context slot: {key}")

    def get_context_snapshot(self) -> dict:
        """Return current context as a dict."""
        return {
            "last_intent": self.last_intent,
            "last_app": self.last_app,
            "last_website": self.last_website,
            "last_contact": self.last_contact,
            "last_message": self.last_message,
            "last_command_text": self.last_command_text,
            "current_goal": self.current_goal,
            "pending_confirmation": self.pending_confirmation,
            "clarification_state": self.clarification_state,
            "is_awaiting_response": self.is_awaiting_response,
        }

    def reset_confirmation(self):
        self.pending_confirmation = None
        self.is_awaiting_response = False

    def reset_clarification(self):
        self.clarification_state = None
        self.is_awaiting_response = False
