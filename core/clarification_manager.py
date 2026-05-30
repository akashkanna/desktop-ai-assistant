"""
Clarification Manager — generates smart clarifying questions
when required entities are missing or confidence is low.
"""
from typing import Optional
from core.intent_parser import ParsedIntent
from logger_config import setup_logger

logger = setup_logger("clarification_manager")

# Maps missing field → clarifying question template
FIELD_QUESTIONS = {
    "contact":     "Who should I send the message to?",
    "message":     "What message should I send?",
    "application": "Which application would you like me to open?",
    "website":     "Which website would you like me to open?",
    "query":       "What would you like me to search for?",
    "text":        "What text should I type?",
    "element":     "Which element or button should I click?",
    "action":      "What action should I perform?",
}

INTENT_QUESTIONS = {
    "unknown":          "I'm not sure what you'd like me to do. Could you rephrase that?",
    "click_element":    "Which button or element should I click? Please describe its location.",
    "type_text":        "What text would you like me to type?",
    "open_website":     "Which website would you like to open?",
    "send_whatsapp_message": "Would you like me to send a WhatsApp message? Who should I message?",
}


class ClarificationManager:
    def __init__(self, confidence_threshold: float = 0.60):
        self.confidence_threshold = confidence_threshold
        logger.info("ClarificationManager ready.")

    def needs_clarification(self, parsed: ParsedIntent) -> bool:
        """Return True if we should ask a clarifying question."""
        if parsed.intent == "unknown":
            return False
        if parsed.confidence < self.confidence_threshold:
            return True
        if parsed.missing_fields:
            return True
        return False

    def get_question(self, parsed: ParsedIntent) -> str:
        """Return the single best clarifying question to ask."""
        # Priority 1: missing required fields
        for field in parsed.missing_fields:
            q = FIELD_QUESTIONS.get(field)
            if q:
                logger.debug(f"Clarification needed for field '{field}': {q}")
                return q

        # Priority 2: low-confidence intent-level question
        if parsed.confidence < self.confidence_threshold:
            q = INTENT_QUESTIONS.get(parsed.intent, INTENT_QUESTIONS["unknown"])
            logger.debug(f"Low-confidence clarification: {q}")
            return q

        # Priority 3: unknown intent
        if parsed.intent == "unknown":
            return INTENT_QUESTIONS["unknown"]

        return "Could you please clarify your request?"

    def build_clarification_state(self, parsed: ParsedIntent) -> dict:
        """Build a state dict to store in context while awaiting answer."""
        return {
            "original_intent": parsed.intent,
            "partial_entities": parsed.entities,
            "missing_fields": list(parsed.missing_fields),
            "question_asked": self.get_question(parsed),
        }

    def merge_clarification_answer(
        self,
        clarification_state: dict,
        answer_text: str,
        parser
    ) -> ParsedIntent:
        """
        After user answers a clarifying question, reconstruct the full command
        by merging the answer into the partial entities.
        """
        intent = clarification_state["original_intent"]
        partial = clarification_state["partial_entities"]
        missing = clarification_state["missing_fields"]

        # Try to parse the answer as a standalone command first
        parsed_answer = parser.parse(answer_text)
        if parsed_answer.intent not in ("unknown",):
            return parsed_answer

        # Otherwise inject the raw answer into the first missing field
        if missing:
            partial[missing[0]] = answer_text.strip()

        # Rebuild a ParsedIntent with filled entities
        from core.intent_parser import ParsedIntent as PI
        still_missing = [f for f in missing[1:] if not partial.get(f)]
        needs_confirm = intent in {"send_whatsapp_message", "close_application", "type_text"}
        merged = PI(
            intent=intent,
            confidence=0.80,
            entities=partial,
            requires_confirmation=needs_confirm,
            missing_fields=still_missing,
        )
        logger.info(f"Merged clarification answer → {merged}")
        return merged
