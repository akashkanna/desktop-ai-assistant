"""
test_context_manager.py
Tests for memory and context management.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory


class TestShortTermMemory:
    def test_add_exchange(self):
        stm = ShortTermMemory()
        stm.add_exchange("open chrome", "Opening Chrome.", {"intent": "open_application"})
        history = stm.get_recent_history(5)
        assert len(history) == 1
        assert history[0]["user"] == "open chrome"

    def test_entity_tracking(self):
        stm = ShortTermMemory()
        stm.update_last_entities({
            "intent": "send_whatsapp_message",
            "entities": {"contact": "Rahul", "message": "Hello"}
        })
        assert stm.last_contact == "Rahul"
        assert stm.last_message == "Hello"

    def test_pending_confirmation(self):
        stm = ShortTermMemory()
        action = {"intent": "send_whatsapp_message", "entities": {}}
        stm.set_pending_confirmation(action)
        assert stm.pending_confirmation is not None
        stm.clear_pending_confirmation()
        assert stm.pending_confirmation is None

    def test_context_summary(self):
        stm = ShortTermMemory()
        stm.last_contact = "Mom"
        stm.last_app = "Chrome"
        summary = stm.get_context_summary()
        assert "Mom" in summary
        assert "Chrome" in summary

    def test_max_history(self):
        stm = ShortTermMemory(max_history=3)
        for i in range(5):
            stm.add_exchange(f"cmd {i}", f"response {i}")
        history = stm.get_recent_history(10)
        assert len(history) == 3  # Capped at max_history


class TestLongTermMemory:
    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            import json
            json.dump({}, f)
            path = f.name

        ltm = LongTermMemory(store_path=path)
        ltm.set("last_contact", "TestUser")
        ltm2 = LongTermMemory(store_path=path)
        assert ltm2.get("last_contact") == "TestUser"
        os.unlink(path)

    def test_frequency_tracking(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            import json
            json.dump({}, f)
            path = f.name

        ltm = LongTermMemory(store_path=path)
        ltm.increment_app_usage("chrome")
        ltm.increment_app_usage("chrome")
        ltm.increment_app_usage("vscode")
        top = ltm.get_top_apps(2)
        assert top[0][0] == "chrome"
        assert top[0][1] == 2
        os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
