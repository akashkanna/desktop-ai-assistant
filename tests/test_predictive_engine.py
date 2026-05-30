"""
Tests for the PredictiveEngine suggestion logic.
"""
import os
import sys
import tempfile
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.predictive_engine import PredictiveEngine
from memory.long_term_memory import LongTermMemory
from core.context_manager import ContextManager


def test_suggest_routine_based_on_top_apps():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump({}, tmp)
        store_path = tmp.name

    try:
        ctx = ContextManager()
        ctx.ltm = LongTermMemory(store_path=store_path)
        ctx.ltm.record_app_usage("vscode")
        ctx.ltm.record_app_usage("chrome")
        ctx.ltm.record_app_usage("spotify")

        engine = PredictiveEngine(ctx)
        suggestion = engine.suggest_routine()
        assert suggestion is not None
        assert "You usually open" in suggestion
    finally:
        os.unlink(store_path)


from unittest.mock import patch


def test_suggest_volume_after_hours():
    ctx = MagicMock()
    ctx.ltm = MagicMock()
    ctx.ltm.get_preference.return_value = 30
    ctx.stm = MagicMock()
    engine = PredictiveEngine(ctx)

    with patch("core.predictive_engine.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 1, 1, 21, 0, 0)
        suggestion = engine.suggest_volume()

    assert suggestion is not None
    assert "prefer volume" in suggestion.lower()
