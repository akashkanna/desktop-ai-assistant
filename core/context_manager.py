"""
Context Manager — merges short-term and long-term memory,
enriches parsed intents with prior context, and handles
pronoun/reference resolution ("him", "it", "same message").
"""
from typing import Optional
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory
from core.intent_parser import ParsedIntent
from logger_config import setup_logger

logger = setup_logger("context_manager")

# Pronouns that should be resolved via context
CONTACT_PRONOUNS = {"him", "her", "them", "he", "she", "they"}
APP_PRONOUNS     = {"it", "that", "this", "the app", "the application"}
MSG_PRONOUNS     = {"same message", "same thing", "that message", "it", "same"}


class ContextManager:
    def __init__(self):
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        logger.info("ContextManager ready.")

    # ------------------------------------------------------------------ #
    # Core enrichment
    # ------------------------------------------------------------------ #
    def enrich(self, parsed: ParsedIntent) -> ParsedIntent:
        """Fill in missing entities from context and resolve pronouns."""
        intent = parsed.intent
        entities = parsed.entities

        # --- Contact resolution ---
        contact = entities.get("contact", "")
        if contact.lower() in CONTACT_PRONOUNS or not contact:
            if self.stm.last_contact:
                logger.info(f"Resolved contact pronoun → '{self.stm.last_contact}'")
                entities["contact"] = self.stm.last_contact
                parsed.missing_fields = [f for f in parsed.missing_fields if f != "contact"]

        # --- Message resolution ---
        message = entities.get("message", "")
        if message.lower() in MSG_PRONOUNS or not message:
            if self.stm.last_message:
                logger.info(f"Resolved message pronoun → '{self.stm.last_message}'")
                entities["message"] = self.stm.last_message
                parsed.missing_fields = [f for f in parsed.missing_fields if f != "message"]

        # --- Application resolution ---
        app = entities.get("application", "")
        if app.lower() in APP_PRONOUNS or not app:
            if self.stm.last_app and intent in ("open_application", "close_application"):
                logger.info(f"Resolved app pronoun → '{self.stm.last_app}'")
                entities["application"] = self.stm.last_app
                parsed.missing_fields = [f for f in parsed.missing_fields if f != "application"]

        # --- Repeat last intent ---
        if intent == "repeat_last":
            parsed = self._rebuild_from_last()

        parsed.entities = entities
        return parsed

    def _rebuild_from_last(self) -> ParsedIntent:
        """Clone the last meaningful intent from short-term memory."""
        history = self.stm.get_history(20)
        for item in reversed(history):
            if item.get("intent") and item["intent"] not in (
                "confirm_yes", "confirm_no", "cancel", "repeat_last", "unknown"
            ):
                logger.info(f"Repeating last intent: {item['intent']}")
                # Re-parse the original text
                from core.intent_parser import IntentParser
                parser = IntentParser()
                return parser.parse(item["text"])
        # Fallback
        from core.intent_parser import ParsedIntent as PI
        return PI("unknown", 0.0, {"raw": "nothing to repeat"}, False, [])

    # ------------------------------------------------------------------ #
    # Update context after execution
    # ------------------------------------------------------------------ #
    def update_after_execution(self, parsed: ParsedIntent, command_text: str):
        """Call this after a command executes successfully."""
        intent = parsed.intent
        entities = parsed.entities

        self.stm.add_to_history("user", command_text, intent=intent)
        self.stm.update_context(
            last_intent=intent,
            last_command_text=command_text,
        )

        if "application" in entities and entities["application"]:
            self.stm.update_context(last_app=entities["application"])
            self.ltm.record_app_usage(entities["application"])

        if "website" in entities and entities["website"]:
            self.stm.update_context(last_website=entities["website"])

        if "contact" in entities and entities["contact"]:
            self.stm.update_context(last_contact=entities["contact"])
            self.ltm.record_contact_usage(entities["contact"])

        if "message" in entities and entities["message"]:
            self.stm.update_context(last_message=entities["message"])

    def add_assistant_response(self, text: str):
        self.stm.add_to_history("assistant", text)

    # ------------------------------------------------------------------ #
    # Confirmation / clarification state
    # ------------------------------------------------------------------ #
    def set_pending_confirmation(self, action_dict: dict):
        self.stm.pending_confirmation = action_dict
        self.stm.is_awaiting_response = True

    def get_pending_confirmation(self) -> Optional[dict]:
        return self.stm.pending_confirmation

    def clear_pending(self):
        self.stm.reset_confirmation()

    def set_clarification(self, state: dict):
        self.stm.clarification_state = state
        self.stm.is_awaiting_response = True

    def get_clarification(self) -> Optional[dict]:
        return self.stm.clarification_state

    def clear_clarification(self):
        self.stm.reset_clarification()

    def is_awaiting(self) -> bool:
        return self.stm.is_awaiting_response

    # ------------------------------------------------------------------ #
    # History / summary
    # ------------------------------------------------------------------ #
    def get_history_text(self, n: int = 10) -> str:
        return self.stm.get_history_text(n)

    def get_context_snapshot(self) -> dict:
        return {
            **self.stm.get_context_snapshot(),
            "top_apps": self.ltm.get_top_apps(3),
            "top_contacts": self.ltm.get_top_contacts(3),
        }

    def save_session_summary(self, summary: str):
        self.ltm.add_session_summary(summary)
