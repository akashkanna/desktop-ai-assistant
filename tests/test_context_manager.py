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
from core.context_manager import ContextManager
from core.intent_parser import ParsedIntent
from unittest.mock import MagicMock


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


class TestContextManagerIntegration:
    def test_enrich_resolves_contact_pronoun(self):
        cm = ContextManager()
        cm.stm.last_contact = "Mom"
        parsed = ParsedIntent(
            intent="send_whatsapp_message",
            confidence=0.9,
            entities={"contact": "him", "message": "Hello"},
            requires_confirmation=True,
            missing_fields=["contact"]
        )

        enriched = cm.enrich(parsed)

        assert enriched.entities["contact"] == "Mom"
        assert "contact" not in enriched.missing_fields

    def test_enrich_repeats_last_intent(self):
        cm = ContextManager()
        cm.stm.add_to_history("user", "open chrome", intent="open_application")
        cm.stm.add_to_history("assistant", "Opening Chrome.")

        parsed = ParsedIntent(
            intent="repeat_last",
            confidence=0.8,
            entities={},
            requires_confirmation=False,
            missing_fields=[]
        )

        result = cm.enrich(parsed)
        assert result.intent == "open_application"
        assert result.entities.get("application") == "chrome"

    def test_update_after_execution_stores_context(self):
        cm = ContextManager()
        cm.ltm.record_app_usage = MagicMock()
        cm.ltm.record_contact_usage = MagicMock()

        parsed = ParsedIntent(
            intent="send_whatsapp_message",
            confidence=0.9,
            entities={"application": "Chrome", "contact": "Jane", "message": "Hello"},
            requires_confirmation=True,
            missing_fields=[]
        )

        cm.update_after_execution(parsed, "open Chrome")

        assert cm.stm.last_app == "Chrome"
        assert cm.stm.last_contact == "Jane"
        assert cm.stm.last_message == "Hello"
        cm.ltm.record_app_usage.assert_called_once_with("Chrome")
        cm.ltm.record_contact_usage.assert_called_once_with("Jane")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
