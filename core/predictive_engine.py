"""
Predictive Engine — suggests likely actions based on usage patterns.
"""
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger("predictive_engine")

class PredictiveEngine:
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.ltm = context_manager.ltm
        self.stm = context_manager.stm
        logger.info("PredictiveEngine initialized.")

    def suggest_routine(self) -> str | None:
        apps = self.ltm.get_top_apps(3)
        if not apps:
            return None

        now = datetime.now()
        if now.hour < 12:
            prefix = "Good morning."
        elif now.hour < 18:
            prefix = "Good afternoon."
        else:
            prefix = "Good evening."

        app_list = ", ".join(apps)
        return f"{prefix} You usually open {app_list} around this time. Would you like me to launch them?"

    def suggest_volume(self) -> str | None:
        volume = self.ltm.get_preference("preferred_volume")
        if volume is None:
            return None

        now = datetime.now()
        if now.hour >= 20:
            return f"You typically prefer volume at {volume} percent after 8 PM. Should I set it for you?"
        return None

    def suggest_workflow(self) -> str | None:
        workflows = self.ltm.get_workflows()
        if not workflows:
            return None
        trigger_names = [wf.get("trigger") or wf["name"] for wf in workflows[:2]]
        return f"I found automation workflows for {', '.join(trigger_names)}. Want me to run one?"
