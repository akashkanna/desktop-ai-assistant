"""
Long-term memory backed by a local JSON file.
Stores user preferences, frequent apps/contacts, and session summaries.
"""
import json
import time
from pathlib import Path
from typing import Any, Optional
from logger_config import setup_logger

logger = setup_logger("long_term_memory")

DEFAULT_STORE = {
    "preferences": {
        "favorite_apps": [],
        "favorite_contacts": [],
        "auto_send_whatsapp": False,
        "preferred_browser": "chrome"
    },
    "frequent_apps": {},
    "frequent_contacts": {},
    "session_summaries": [],
    "last_updated": None
}

class LongTermMemory:
    def __init__(self, store_path: str = "memory/memory_store.json"):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> dict:
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Long-term memory loaded from {self.store_path}")
                return data
            except Exception as e:
                logger.error(f"Failed to load memory store: {e}")
        return dict(DEFAULT_STORE)

    def save(self):
        self._data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Long-term memory saved.")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    # ------------------------------------------------------------------ #
    # App usage tracking
    # ------------------------------------------------------------------ #
    def record_app_usage(self, app_name: str):
        freq = self._data.setdefault("frequent_apps", {})
        freq[app_name] = freq.get(app_name, 0) + 1
        self.save()

    def get_top_apps(self, n: int = 5) -> list:
        freq = self._data.get("frequent_apps", {})
        return sorted(freq, key=freq.get, reverse=True)[:n]

    # ------------------------------------------------------------------ #
    # Contact usage tracking
    # ------------------------------------------------------------------ #
    def record_contact_usage(self, contact: str):
        freq = self._data.setdefault("frequent_contacts", {})
        freq[contact] = freq.get(contact, 0) + 1
        self.save()

    def get_top_contacts(self, n: int = 5) -> list:
        freq = self._data.get("frequent_contacts", {})
        return sorted(freq, key=freq.get, reverse=True)[:n]

    # ------------------------------------------------------------------ #
    # Preferences
    # ------------------------------------------------------------------ #
    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._data.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value: Any):
        self._data.setdefault("preferences", {})[key] = value
        self.save()

    # ------------------------------------------------------------------ #
    # Session summaries
    # ------------------------------------------------------------------ #
    def add_session_summary(self, summary: str):
        summaries = self._data.setdefault("session_summaries", [])
        summaries.append({
            "summary": summary,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        # Keep only last 20 summaries
        if len(summaries) > 20:
            self._data["session_summaries"] = summaries[-20:]
        self.save()

    def get_recent_summaries(self, n: int = 3) -> list:
        summaries = self._data.get("session_summaries", [])
        return summaries[-n:]

    def get_full_store(self) -> dict:
        return self._data
