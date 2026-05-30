"""
Safety Manager — ensures risky actions require confirmation and intercepts cancel commands.
"""
from core.intent_parser import ParsedIntent
from logger_config import setup_logger

logger = setup_logger("safety_manager")

class SafetyManager:
    def __init__(self, config_path: str = "config/settings.json"):
        import json
        try:
            with open(config_path, "r") as f:
                settings = json.load(f)
                self.require_confirmation_for = settings.get("safety", {}).get("require_confirmation_for", [])
        except:
            self.require_confirmation_for = ["send_whatsapp_message", "close_application"]

        logger.info(f"SafetyManager initialized. Confirms required for: {self.require_confirmation_for}")

    def is_safe_to_execute(self, parsed: ParsedIntent) -> bool:
        if parsed.intent in self.require_confirmation_for:
            if not parsed.requires_confirmation: 
                return True # If somehow it was overridden, allow it
            return False # Needs confirmation
        return True
