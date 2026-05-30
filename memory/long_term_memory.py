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
        "preferred_browser": "chrome",
        "preferred_volume": None,
        "preferred_theme": None,
        "night_light_enabled": None
    },
    "frequent_apps": {},
    "frequent_contacts": {},
    "favorite_websites": [],
    "automation_rules": [],
    "custom_commands": {},
    "device_info": {},
    "notifications": [],
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

    def add_workflow(self, workflow: dict):
        workflows = self._data.setdefault("automation_rules", [])
        existing = next((w for w in workflows if w["name"].lower() == workflow["name"].lower()), None)
        if existing:
            workflows.remove(existing)
        workflows.append(workflow)
        self.save()

    def get_workflows(self) -> list:
        return list(self._data.get("automation_rules", []))

    def get_workflow(self, name: str) -> dict | None:
        return next((w for w in self.get_workflows() if w["name"].lower() == name.lower()), None)

    def remove_workflow(self, name: str) -> bool:
        workflows = self._data.setdefault("automation_rules", [])
        before = len(workflows)
        self._data["automation_rules"] = [w for w in workflows if w["name"].lower() != name.lower()]
        removed = len(workflows) != len(self._data["automation_rules"])
        if removed:
            self.save()
        return removed

    def add_custom_command(self, command_name: str, command_value: str):
        custom = self._data.setdefault("custom_commands", {})
        custom[command_name] = command_value
        self.save()

    def get_custom_commands(self) -> dict:
        return dict(self._data.get("custom_commands", {}))

    def add_favorite_website(self, website: str):
        favorites = self._data.setdefault("favorite_websites", [])
        if website not in favorites:
            favorites.append(website)
            self.save()

    def get_favorite_websites(self) -> list:
        return list(self._data.get("favorite_websites", []))

    def record_device_info(self, key: str, value: Any):
        info = self._data.setdefault("device_info", {})
        info[key] = value
        self.save()

    def get_device_info(self, key: str, default: Any = None) -> Any:
        return self._data.get("device_info", {}).get(key, default)

    def add_notification(self, notification: dict):
        notifications = self._data.setdefault("notifications", [])
        notifications.append(notification)
        self.save()

    def get_notifications(self, category: str | None = None) -> list:
        notifications = list(self._data.get("notifications", []))
        if category:
            return [n for n in notifications if n.get("category") == category]
        return notifications

    def get_full_store(self) -> dict:
        return self._data
