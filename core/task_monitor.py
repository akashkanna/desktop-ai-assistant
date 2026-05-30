"""
Task Monitor — tracks task state and progress.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from logger_config import setup_logger

logger = setup_logger("task_monitor")

@dataclass
class TaskStatus:
    task_id: str
    name: str
    status: str = "pending"
    progress: int = 0
    message: str = ""
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

class TaskMonitor:
    def __init__(self):
        self.tasks: dict[str, TaskStatus] = {}
        logger.info("TaskMonitor initialized.")

    def create_task(self, name: str, message: str = "") -> TaskStatus:
        task_id = str(uuid.uuid4())
        task = TaskStatus(task_id=task_id, name=name, message=message)
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id} ({name})")
        return task

    def update_task(self, task_id: str, status: str, progress: int | None = None, message: str | None = None) -> TaskStatus | None:
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.status = status
        if progress is not None:
            task.progress = max(0, min(100, progress))
        if message is not None:
            task.message = message
        task.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Task {task_id} updated to {status}")
        return task

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        task.status = "cancelled"
        task.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Task {task_id} cancelled")
        return True

    def get_task(self, task_id: str) -> TaskStatus | None:
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[TaskStatus]:
        return list(self.tasks.values())
