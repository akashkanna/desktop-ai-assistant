"""
Intent Parser — converts raw text into structured intent objects.
Uses keyword/pattern matching with confidence scoring.
No external AI API required (offline-first design).
"""
import re
from typing import Optional
from logger_config import setup_logger

logger = setup_logger("intent_parser")

# -----------------------------------------------------------------------
# Intent patterns: each entry is (intent_name, patterns, required_entities)
# Patterns are checked in ORDER — put more specific ones FIRST.
# -----------------------------------------------------------------------
INTENT_PATTERNS = [

    # ── Chit-chat / conversational (check early to avoid being swallowed) ──
    ("greeting",
     [r"^(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|howdy)\b"],
     []),

    ("ask_name",
     [r"(your\s+name|who\s+are\s+you|what\s+are\s+you\s+called|tell\s+me\s+your\s+name)"],
     []),

    ("ask_time",
     [r"(what(?:'s|\s+is)\s+the\s+time|what\s+time\s+is\s+it|time\s+now|current\s+time|tell\s+me\s+the\s+time)"],
     []),

    ("ask_date",
     [r"(what(?:'s|\s+is)\s+the\s+date|what\s+day\s+is\s+it|today(?:'s)?\s+date|current\s+date)"],
     []),

    ("ask_how_are_you",
     [r"(how\s+are\s+you|how\s+do\s+you\s+do|how(?:'s|\s+is)\s+it\s+going|are\s+you\s+okay)"],
     []),

    ("ask_capabilities",
     [r"(what\s+can\s+you\s+do|show\s+commands|list\s+commands|your\s+capabilities|help\s+me|what\s+do\s+you\s+do)"],
     []),

    ("repeat_last",
     [r"(say\s+that\s+again|say\s+again|repeat\s+(that|last|it|this)?|again\s+please|tell\s+me\s+again|what\s+did\s+you\s+say)"],
     []),

    # ── Confirm / Yes / No ─────────────────────────────────────────────
    ("confirm_yes",
     [r"^(yes|yeah|yep|yup|sure|ok|okay|go\s+ahead|do\s+it|send\s+it|confirm|proceed|of\s+course|absolutely)$"],
     []),

    ("confirm_no",
     [r"^(no|nope|don'?t|do\s+not|skip|decline|never\s+mind|cancel|abort|stop|forget\s+it)$"],
     []),

    # ── Cancel ─────────────────────────────────────────────────────────
    ("cancel",
     [r"^(cancel|stop|abort|never\s+mind|forget\s+it|cancel\s+that)$",
      r"(cancel\s+shutdown|abort\s+shutdown)"],
     []),

    # ── Volume ─────────────────────────────────────────────────────────
    ("volume_control",
     [r"(increase|raise|turn\s+up)\s+(?:the\s+|my\s+|system\s+)?volume(?:\s+(?:by\s+)?(\d+)%?)?",
      r"(decrease|lower|reduce|turn\s+down)\s+(?:the\s+|my\s+|system\s+)?volume(?:\s+(?:by\s+)?(\d+)%?)?",
      r"(mute)\s+(?:the\s+|my\s+|system\s+)?(?:volume|sound|mic|microphone)?",
      r"(unmute)\s+(?:the\s+|my\s+|system\s+)?(?:volume|sound|mic|microphone)?",
      r"(change|control|set|adjust)\s+(?:the\s+|my\s+|system\s+)?volume(?:\s+to\s+(\d+)%?)?",
      r"(?:set\s+)?(?:the\s+|my\s+|system\s+)?volume\s+to\s+(\d+)%?",
      r"volume\s+(up|down)\s*(\d+)?"],
     ["action"]),

    # ── System power ───────────────────────────────────────────────────
    ("lock_screen",
     [r"(lock\s+(the\s+)?(?:screen|computer|pc|system)|screen\s+lock)"],
     []),

    ("shutdown",
     [r"(shut\s+down|shutdown|power\s+off)\s+(?:the\s+|my\s+)?(computer|pc|system|laptop)?"],
     []),

    ("restart",
     [r"(restart|reboot)\s+(?:the\s+|my\s+)?(computer|pc|system|laptop)?"],
     []),

    ("cancel_shutdown",
     [r"(cancel\s+shutdown|abort\s+shutdown|stop\s+shutdown)"],
     []),

    ("sleep_mode",
     [r"(sleep|put.+sleep|sleep\s+mode|go\s+to\s+sleep|standby)"],
     []),

    # ── Window management ──────────────────────────────────────────────
    ("minimize_window",
     [r"(minimise|minimize)\s+(.+)",
      r"(minimise|minimize)\s+(?:this|the|my)?\s*(window|tab|screen)?"],
     []),

    ("maximize_window",
     [r"(maximise|maximize)\s+(.+)",
      r"(maximise|maximize)\s+(?:this|the|my)?\s*(window|tab|screen)?"],
     []),

    # ── Close application ──────────────────────────────────────────────
    ("close_application",
     [r"close\s+(.+)",
      r"quit\s+(.+)",
      r"exit\s+(.+)",
      r"kill\s+(.+)"],
     []),

    # ── Screenshot ─────────────────────────────────────────────────────
    ("take_screenshot",
     [r"(take\s+(?:a\s+)?screenshot|capture\s+(?:the\s+)?screen|screenshot)"],
     []),

    # ── WhatsApp messaging ─────────────────────────────────────────────
    ("send_whatsapp_message",
     [r"send\s+(?:whatsapp\s+)?(?:message\s+)?to\s+(\w[\w\s]*)\s+saying\s+(.+)",
      r"send\s+(?:whatsapp\s+)?(?:message\s+)?to\s+(\w[\w\s]*):\s*(.+)",
      r"whatsapp\s+(\w[\w\s]*)\s+(?:saying|that)\s+(.+)",
      r"message\s+(\w[\w\s]*)\s+(?:saying|that|:)\s+(.+)",
      r"send\s+(.+)\s+to\s+(\w[\w\s]*)\s+on\s+whatsapp",
      r"send\s+(?:a\s+)?(?:whatsapp\s+)?message\s+to\s+(\w[\w\s]*)",
      r"text\s+(\w[\w\s]*)\s+(?:saying|that)\s+(.+)"],
     ["contact"]),

    # ── YouTube search ─────────────────────────────────────────────────
    ("search_youtube",
     [r"(?:search|play|find|look\s+for)\s+(.+?)\s+(?:on\s+)?youtube",
      r"youtube\s+(.+)"],
     ["query"]),

    # ── Web search ─────────────────────────────────────────────────────
    ("search_web",
     [r"search\s+(?:for\s+)?(.+?)\s+on\s+(google|bing|youtube|yahoo)",
      r"(?:google|look\s+up|search\s+for|find)\s+(.+)"],
     ["query"]),

    # ── Website / browser ──────────────────────────────────────────────
    ("open_website",
     [r"open\s+(.+?)\s+(?:website|site|page|url)",
      r"go\s+to\s+(.+)",
      r"visit\s+(.+)",
      r"browse\s+(.+)",
      r"navigate\s+to\s+(.+)"],
     ["website"]),

    # ── Type text ──────────────────────────────────────────────────────
    ("type_text",
     [r"(?:type|write|input)\s+(.+)"],
     ["text"]),

    # ── Click ──────────────────────────────────────────────────────────
    ("click_element",
     [r"click\s+(?:on\s+)?(?:the\s+)?(.+?)(?:\s+button)?$",
      r"press\s+(?:the\s+)?(.+?)(?:\s+button)?$"],
     ["element"]),

    # ── Open application (LAST — very broad pattern) ───────────────────
    ("open_application",
     [r"open\s+(.+)",
      r"launch\s+(.+)",
      r"start\s+(.+)",
      r"run\s+(.+)"],
     ["application"]),

    # ── Help ───────────────────────────────────────────────────────────
    ("help",
     [r"^help$"],
     []),
]

# -----------------------------------------------------------------------
# Stop-word lists for entity cleaning
# -----------------------------------------------------------------------
SKIP_WORDS_APP = {
    "open", "launch", "start", "run", "the", "an", "a", "my", "our",
    "application", "app", "program", "software", "please"
}
SKIP_WORDS_WEB = {
    "open", "go", "to", "visit", "browse", "navigate",
    "the", "website", "site", "page", "url", "web"
}
SKIP_WORDS_CLOSE = {
    "close", "quit", "exit", "kill", "the", "an", "a", "my",
    "this", "application", "app", "window", "tab"
}
SKIP_WORDS_WIN = {
    "minimise", "minimize", "maximise", "maximize", "the", "a", "my", "this",
    "window", "tab", "screen"
}


def _clean(text: str, skip: set) -> str:
    words = text.lower().split()
    return " ".join(w for w in words if w not in skip).strip()


def _extract_entities(intent: str, match: re.Match, raw: str) -> dict:
    """Map regex capture groups to named entities based on intent."""
    groups = [g.strip() for g in match.groups() if g]
    entities: dict = {}

    if intent == "open_application":
        entities["application"] = _clean(groups[0], SKIP_WORDS_APP) if groups else ""

    elif intent == "close_application":
        raw_app = groups[0] if groups else ""
        entities["application"] = _clean(raw_app, SKIP_WORDS_CLOSE)

    elif intent == "minimize_window":
        # groups could be ("minimise", "app_name") or ("minimise", "window")
        app = groups[1] if len(groups) > 1 else ""
        entities["application"] = _clean(app, SKIP_WORDS_WIN)

    elif intent == "maximize_window":
        app = groups[1] if len(groups) > 1 else ""
        entities["application"] = _clean(app, SKIP_WORDS_WIN)

    elif intent == "send_whatsapp_message":
        if len(groups) >= 2:
            if re.search(r"send\s+(.+)\s+to\s+(\w+)\s+on\s+whatsapp", raw.lower()):
                entities["message"] = groups[0]
                entities["contact"] = groups[1]
            else:
                entities["contact"] = groups[0]
                entities["message"] = groups[1]
        elif len(groups) == 1:
            entities["contact"] = groups[0]

    elif intent == "open_website":
        entities["website"] = _clean(groups[0], SKIP_WORDS_WEB) if groups else ""

    elif intent == "search_web":
        entities["query"] = groups[0] if groups else ""
        entities["engine"] = groups[1].lower() if len(groups) > 1 else "google"

    elif intent == "search_youtube":
        entities["query"] = groups[0] if groups else ""

    elif intent == "type_text":
        entities["text"] = groups[0] if groups else ""

    elif intent == "click_element":
        entities["element"] = groups[0] if groups else ""

    elif intent == "volume_control":
        raw_lower = raw.lower()
        # Determine action
        if re.search(r"(increase|raise|turn\s+up|volume\s+up)", raw_lower):
            entities["action"] = "increase"
        elif re.search(r"(decrease|lower|reduce|turn\s+down|volume\s+down)", raw_lower):
            entities["action"] = "decrease"
        elif re.search(r"\bmute\b", raw_lower):
            entities["action"] = "mute"
        elif re.search(r"\bunmute\b", raw_lower):
            entities["action"] = "unmute"
        else:
            entities["action"] = "set"

        # Extract numeric level if any
        num_match = re.search(r"(\d+)", raw_lower)
        if num_match:
            entities["level"] = int(num_match.group(1))
        else:
            entities["level"] = None

    return entities


def _compute_confidence(intent: str, text: str, entities: dict, required: list) -> float:
    """Heuristic confidence scorer."""
    base = 0.85

    # Missing required entities reduce confidence
    missing = [f for f in required if not entities.get(f)]
    base -= 0.15 * len(missing)

    # Short command → less confidence for complex intents
    no_entity_intents = {
        "cancel", "confirm_yes", "confirm_no", "take_screenshot",
        "help", "greeting", "ask_time", "ask_date", "ask_name",
        "ask_how_are_you", "ask_capabilities", "repeat_last",
        "lock_screen", "shutdown", "restart", "minimize_window", "maximize_window"
    }
    if len(text.split()) < 3 and intent not in no_entity_intents:
        base -= 0.10

    return round(max(0.0, min(1.0, base)), 2)


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------
class ParsedIntent:
    def __init__(self, intent: str, confidence: float, entities: dict,
                 requires_confirmation: bool, missing_fields: list):
        self.intent = intent
        self.confidence = confidence
        self.entities = entities
        self.requires_confirmation = requires_confirmation
        self.missing_fields = missing_fields

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "requires_confirmation": self.requires_confirmation,
            "missing_fields": self.missing_fields,
        }

    def __repr__(self):
        return f"<ParsedIntent intent={self.intent} conf={self.confidence} entities={self.entities}>"


CONFIRMATION_INTENTS = {
    "send_whatsapp_message", "type_text",
    "shutdown", "restart", "lock_screen"
}

class IntentParser:
    def __init__(self, confidence_threshold: float = 0.60):
        self.confidence_threshold = confidence_threshold
        self._compiled = self._compile_patterns()
        logger.info("IntentParser initialised.")

    def _compile_patterns(self):
        compiled = []
        for intent, patterns, required in INTENT_PATTERNS:
            for pat in patterns:
                try:
                    compiled.append((intent, re.compile(pat, re.IGNORECASE), required))
                except re.error as e:
                    logger.error(f"Bad regex for {intent}: {pat} — {e}")
        return compiled

    def parse(self, text: str) -> ParsedIntent:
        """Parse raw text into a ParsedIntent."""
        text = text.strip()
        logger.debug(f"Parsing: '{text}'")

        for intent, pattern, required in self._compiled:
            match = pattern.search(text)
            if match:
                entities = _extract_entities(intent, match, text)
                missing = [f for f in required if not entities.get(f)]
                confidence = _compute_confidence(intent, text, entities, required)
                needs_confirm = intent in CONFIRMATION_INTENTS

                result = ParsedIntent(
                    intent=intent,
                    confidence=confidence,
                    entities=entities,
                    requires_confirmation=needs_confirm,
                    missing_fields=missing
                )
                logger.info(f"Matched: {result}")
                return result

        # Unknown intent
        result = ParsedIntent(
            intent="unknown",
            confidence=0.0,
            entities={"raw": text},
            requires_confirmation=False,
            missing_fields=[]
        )
        logger.warning(f"No intent matched for: '{text}'")
        return result
