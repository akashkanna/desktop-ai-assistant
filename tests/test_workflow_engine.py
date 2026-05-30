"""
Tests for the WorkflowEngine feature.
"""
import os
import sys
import tempfile
import json
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.workflow_engine import WorkflowEngine
from memory.long_term_memory import LongTermMemory


def make_workflow_engine(temp_path):
    router = MagicMock()
    router.execute.return_value = "step completed"
    router._dispatch_text.return_value = "text step completed"
    memory = LongTermMemory(store_path=temp_path)
    return WorkflowEngine(router, memory), router, memory


def test_create_and_list_workflow():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump({}, tmp)
        store_path = tmp.name

    try:
        engine, router, memory = make_workflow_engine(store_path)
        workflow = engine.create_workflow(
            name="Start Work",
            steps=[{"text": "open vscode"}, {"text": "set volume to 30%"}],
            trigger="Start Work",
        )

        assert workflow["name"] == "Start Work"
        workflows = engine.list_workflows()
        assert any(w["name"] == "Start Work" for w in workflows)
        assert engine.get_workflow("Start Work") is not None
    finally:
        os.unlink(store_path)


def test_remove_workflow():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump({}, tmp)
        store_path = tmp.name

    try:
        engine, _, _ = make_workflow_engine(store_path)
        engine.create_workflow("Night Routine", steps=[{"text": "close chrome"}])
        assert engine.remove_workflow("Night Routine")
        assert engine.get_workflow("Night Routine") is None
    finally:
        os.unlink(store_path)


def test_execute_workflow_runs_steps():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump({}, tmp)
        store_path = tmp.name

    try:
        engine, router, _ = make_workflow_engine(store_path)
        engine.create_workflow("Startup", steps=[{"text": "open chrome"}, {"text": "search for Python tutorials"}])
        result = engine.execute_workflow("Startup")
        assert "text step completed" in result
        assert router._dispatch_text.call_count == 2
    finally:
        os.unlink(store_path)
