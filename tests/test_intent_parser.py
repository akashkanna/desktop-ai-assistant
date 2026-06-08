"""
test_intent_parser.py
Basic tests for the intent parser (keyword fallback mode).
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock


def make_parser():
    """Create a parser with a mock context manager."""
    from core.intent_parser import IntentParser
    ctx = MagicMock()
    ctx.build_system_prompt.return_value = ""
    ctx.get_recent_messages_for_ai.return_value = []
    settings = {"confidence_threshold": 0.65, "anthropic_model": "test"}
    return IntentParser(ctx, settings)


class TestFallbackParser:
    def test_open_application_variants(self):
        parser = make_parser()
        cases = {
            "open Chrome": "chrome",
            "open the Chrome": "chrome",
            "launch Chrome": "chrome",
            "launch the chrome": "chrome",
            "hey jarvis open chrome": "chrome",
            "please open chrome": "chrome",
            "can you launch google chrome": "chrome",
            "start chrome": "chrome",
            "open browser": "chrome",
        }
        for phrase, expected_app in cases.items():
            result = parser.parse(phrase)
            assert result.intent == "open_application", f"{phrase!r} -> {result.intent}"
            assert result.entities["application"] == expected_app, f"{phrase!r} -> {result.entities}"

    def test_open_application(self):
        parser = make_parser()
        result = parser._parse_with_fallback("open Chrome")
        assert result["intent"] == "open_application"
        assert result["entities"]["application"] == "chrome"

    def test_take_screenshot(self):
        parser = make_parser()
        result = parser._parse_with_fallback("take a screenshot")
        assert result["intent"] == "take_screenshot"

    def test_whatsapp_with_contact_and_message(self):
        parser = make_parser()
        result = parser._parse_with_fallback("send whatsapp message to Rahul saying I will be late")
        assert result["intent"] == "send_whatsapp_message"
        assert "rahul" in result["entities"].get("contact", "").lower()
        assert "i will be late" in result["entities"].get("message", "").lower()

    def test_whatsapp_missing_message(self):
        parser = make_parser()
        result = parser._parse_with_fallback("send message to Mom")
        assert result["intent"] == "send_whatsapp_message"
        assert "message" in result["missing_fields"]

    def test_search_web(self):
        parser = make_parser()
        result = parser._parse_with_fallback("search for Python tutorials")
        assert result["intent"] == "search_web"

    def test_clipboard_shortcuts(self):
        parser = make_parser()

        result = parser._parse_with_fallback("copy this")
        assert result["intent"] == "copy"

        result = parser._parse_with_fallback("paste here")
        assert result["intent"] == "paste"

        result = parser._parse_with_fallback("cut this")
        assert result["intent"] == "cut"

        result = parser._parse_with_fallback("copy control c")
        assert result["intent"] == "copy"

        result = parser._parse_with_fallback("select all")
        assert result["intent"] == "select_all"

        result = parser._parse_with_fallback("select")
        assert result["intent"] == "select_all"

    def test_refresh_shortcut(self):
        parser = make_parser()
        result = parser._parse_with_fallback("refresh")
        assert result["intent"] == "refresh_ui"

        result = parser._parse_with_fallback("hard refresh")
        assert result["intent"] == "refresh_ui"

    def test_refresh_aliases(self):
        parser = make_parser()
        for phrase in ["refresh refresh", "reload", "update screen", "reload screen", "refresh dashboard"]:
            result = parser._parse_with_fallback(phrase)
            assert result["intent"] == "refresh_ui", f"{phrase} should map to refresh_ui"

    def test_confirm_action(self):
        parser = make_parser()
        result = parser._parse_with_fallback("yes")
        assert result["intent"] == "confirm_action"

    def test_cancel(self):
        parser = make_parser()
        result = parser._parse_with_fallback("cancel")
        assert result["intent"] == "cancel_task"

    def test_unknown(self):
        parser = make_parser()
        result = parser._parse_with_fallback("xyzzy frobulate the quux")
        assert result["intent"] == "unknown"

    def test_clarification_question_generation(self):
        parser = make_parser()
        q = parser.get_clarification_question("send_whatsapp_message", ["contact"])
        assert "who" in q.lower() or "contact" in q.lower() or "send" in q.lower()

    def test_clarification_both_missing(self):
        parser = make_parser()
        q = parser.get_clarification_question("send_whatsapp_message", ["contact", "message"])
        assert len(q) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
