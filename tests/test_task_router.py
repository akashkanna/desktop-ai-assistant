"""
test_task_router.py
Tests for the task router logic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch


def make_router():
    ctx = MagicMock()
    ctx.get_pending_confirmation.return_value = None
    ctx.get_clarification.return_value = None
    settings = {"confidence_threshold": 0.65}
    router_cls = __import__("core.task_router", fromlist=["TaskRouter"]).TaskRouter
    router = router_cls(settings=settings, context_manager=ctx)
    return router, ctx


class TestTaskRouter:
    def test_low_confidence_triggers_clarification(self):
        router, ctx = make_router()
        clarifications = []
        router.on_clarification_needed = lambda q, i: clarifications.append(q)

        intent = {
            "intent": "open_application",
            "confidence": 0.3,  # below threshold
            "entities": {"application": "chrome"},
            "requires_confirmation": False,
            "missing_fields": [],
            "response": ""
        }
        success, msg = router.route(intent)
        assert not success
        assert len(clarifications) == 1

    def test_missing_fields_triggers_clarification(self):
        router, ctx = make_router()
        clarifications = []
        router.on_clarification_needed = lambda q, i: clarifications.append(q)

        intent = {
            "intent": "send_whatsapp_message",
            "confidence": 0.9,
            "entities": {"contact": "Mom"},
            "requires_confirmation": True,
            "missing_fields": ["message"],
            "response": ""
        }
        success, msg = router.route(intent)
        assert len(clarifications) == 1
        assert "message" in clarifications[0].lower() or "say" in clarifications[0].lower()

    def test_cancel_clears_pending(self):
        router, ctx = make_router()
        ctx.get_pending_confirmation.return_value = {"intent": "send_whatsapp_message"}
        ctx.get_clarification.return_value = None

        intent = {
            "intent": "cancel_task",
            "confidence": 0.95,
            "entities": {},
            "requires_confirmation": False,
            "missing_fields": [],
            "response": "Cancelled"
        }
        success, msg = router.route(intent)
        assert success
        ctx.clear_pending_confirmation.assert_called()

    def test_requires_confirmation_sets_pending(self):
        router, ctx = make_router()
        confirmations = []
        router.on_confirmation_needed = lambda a, m: confirmations.append(m)

        intent = {
            "intent": "send_whatsapp_message",
            "confidence": 0.92,
            "entities": {"contact": "Rahul", "message": "I will be late"},
            "requires_confirmation": True,
            "missing_fields": [],
            "response": "Should I send this message to Rahul?"
        }

        # Mock draft_message
        with patch.object(router, '_get_whatsapp') as mock_wa:
            mock_wa.return_value.draft_message.return_value = (True, "Message drafted.")
            success, msg = router.route(intent)

        ctx.set_pending_confirmation.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
