"""
Workflow Engine — manages user-defined automation routines.
"""
import json
import threading
import time
from typing import Any
from logger_config import setup_logger
from core.intent_parser import ParsedIntent

logger = setup_logger("workflow_engine")

class WorkflowEngine:
    def __init__(self, task_router, memory):
        self.task_router = task_router
        self.memory = memory
        logger.info("WorkflowEngine initialized.")

    def create_workflow(
        self,
        name: str,
        steps: list[dict[str, Any]],
        trigger: str | None = None,
        condition: str | None = None,
        delay: int | None = None,
    ) -> dict:
        workflow = {
            "name": name,
            "trigger": trigger,
            "condition": condition,
            "delay": delay,
            "steps": steps,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.memory.add_workflow(workflow)
        return workflow

    def get_workflow(self, name: str) -> dict | None:
        return self.memory.get_workflow(name)

    def find_workflow_for_text(self, text: str) -> dict | None:
        lowered = text.strip().lower()
        for workflow in self.list_workflows():
            name = workflow.get("name", "").lower()
            trigger = str(workflow.get("trigger", "")).lower()
            if name and name in lowered:
                return workflow
            if trigger and trigger in lowered:
                return workflow
        return None

    def list_workflows(self) -> list[dict[str, Any]]:
        return self.memory.get_workflows()

    def remove_workflow(self, name: str) -> bool:
        return self.memory.remove_workflow(name)

    def execute_workflow(self, name: str) -> str:
        workflow = self.get_workflow(name)
        if not workflow:
            return f"I could not find a workflow named '{name}'."

        if workflow.get("delay"):
            timer = threading.Timer(workflow["delay"], self._run_steps, [workflow["steps"]])
            timer.start()
            return f"Scheduled workflow '{name}' to run in {workflow['delay']} seconds."

        return self._run_steps(workflow["steps"])

    def _run_steps(self, steps: list[dict[str, Any]]) -> str:
        results = []
        for step in steps:
            if "text" in step and step["text"]:
                result = self.task_router._dispatch_text(step["text"])
            else:
                intent = step.get("intent")
                entities = step.get("entities", {})
                if not intent:
                    continue
                metadata = ParsedIntent(
                    intent=intent,
                    confidence=0.95,
                    entities=entities,
                    requires_confirmation=False,
                    missing_fields=[],
                )
                result = self.task_router.execute(metadata)

            results.append(result)
            time.sleep(step.get("pause", 0.5))
        return "\n".join(results)
