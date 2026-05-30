"""
Assistant Controller — central brain.
Wires STT, TTS, Intent Parser, Context, Task Router, and UI signals.
"""
import threading
from core.intent_parser import IntentParser
from core.context_manager import ContextManager
from core.clarification_manager import ClarificationManager
from core.safety_manager import SafetyManager
from core.task_router import TaskRouter
from voice.text_to_speech import TextToSpeech
from voice.speech_to_text import SpeechToText
from logger_config import setup_logger

logger = setup_logger("assistant_controller")


class AssistantController:
    def __init__(self, ui_callback=None):
        self.ui_callback = ui_callback

        self.intent_parser = IntentParser()
        self.context_manager = ContextManager()
        self.clarification_manager = ClarificationManager()
        self.safety_manager = SafetyManager()
        self.task_router = TaskRouter()

        self.tts = TextToSpeech()
        self.stt = SpeechToText()

        self.is_listening = False
        self.listen_thread = None

        logger.info("AssistantController initialized.")

    # ─────────────────────────── UI helper ───────────────────────────

    def update_ui(self, status=None, user_text=None, assistant_text=None,
                  is_muted=None, avatar_state=None):
        if self.ui_callback:
            self.ui_callback(
                status=status,
                user_text=user_text,
                assistant_text=assistant_text,
                is_muted=is_muted,
                avatar_state=avatar_state,
            )

    def toggle_mute(self):
        self.tts.is_muted = not self.tts.is_muted
        self.update_ui(is_muted=self.tts.is_muted)

    # ─────────────────────────── speak ───────────────────────────────

    def speak(self, text: str):
        self.update_ui(assistant_text=text, status="Speaking…", avatar_state="speaking")
        self.tts.speak(text, on_done=self._on_speak_done)
        self.context_manager.add_assistant_response(text)

    def _on_speak_done(self):
        if self.is_listening:
            self.update_ui(status="Listening…", avatar_state="listening")
        else:
            self.update_ui(status="Idle", avatar_state="idle")

    # ─────────────────────────── input processing ────────────────────

    def process_text_input(self, text: str):
        if not text:
            return

        logger.info(f"Processing: {text}")
        self.update_ui(user_text=text, status="Thinking…", avatar_state="thinking")

        # 1. Awaiting state (confirmation / clarification)
        if self.context_manager.is_awaiting():
            self._handle_awaiting_state(text)
            return

        # 2. Parse
        parsed = self.intent_parser.parse(text)

        # 3. Enrich with context
        parsed = self.context_manager.enrich(parsed)

        # 4. Clarification needed?
        if self.clarification_manager.needs_clarification(parsed):
            state = self.clarification_manager.build_clarification_state(parsed)
            self.context_manager.set_clarification(state)
            self.speak(state["question_asked"])
            return

        # 5. Safety / confirmation needed?
        if not self.safety_manager.is_safe_to_execute(parsed):
            self.context_manager.set_pending_confirmation(parsed.to_dict())
            self.speak(f"Do you want me to proceed with: {parsed.intent.replace('_', ' ')}?")
            return

        # 6. Execute
        self._execute_parsed_intent(parsed, text)

    def _handle_awaiting_state(self, text: str):
        pending = self.context_manager.get_pending_confirmation()
        if pending:
            answer = self.intent_parser.parse(text)
            if answer.intent == "confirm_yes":
                self.context_manager.clear_pending()
                from core.intent_parser import ParsedIntent
                pi = ParsedIntent(**pending)
                self._execute_parsed_intent(pi, text)
            elif answer.intent in ("confirm_no", "cancel"):
                self.context_manager.clear_pending()
                self.speak("Action cancelled.")
            else:
                self.speak("Please say yes to confirm, or no to cancel.")
            return

        clr = self.context_manager.get_clarification()
        if clr:
            if self.intent_parser.parse(text).intent == "cancel":
                self.context_manager.clear_clarification()
                self.speak("Cancelled.")
                return
            merged = self.clarification_manager.merge_clarification_answer(
                clr, text, self.intent_parser)
            self.context_manager.clear_clarification()
            if self.clarification_manager.needs_clarification(merged):
                ns = self.clarification_manager.build_clarification_state(merged)
                self.context_manager.set_clarification(ns)
                self.speak(ns["question_asked"])
            elif not self.safety_manager.is_safe_to_execute(merged):
                self.context_manager.set_pending_confirmation(merged.to_dict())
                self.speak(f"Do you want me to: {merged.intent.replace('_', ' ')}?")
            else:
                self._execute_parsed_intent(merged, text)

    def _execute_parsed_intent(self, parsed, original_text: str):
        if parsed.intent == "cancel":
            self.speak("Cancelled.")
            return
        self.update_ui(status="Executing…", avatar_state="thinking")
        result = self.task_router.execute(parsed)
        self.context_manager.update_after_execution(parsed, original_text)
        self.speak(result)

    # ─────────────────────────── voice loop ──────────────────────────

    def start_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.update_ui(status="Listening…", avatar_state="listening")

        if self.listen_thread and self.listen_thread.is_alive():
            return

        def _loop():
            while self.is_listening:
                text = self.stt.listen()
                if text and self.is_listening:
                    self.process_text_input(text)

        self.listen_thread = threading.Thread(target=_loop, daemon=True)
        self.listen_thread.start()

    def stop_listening(self):
        self.is_listening = False
        self.update_ui(status="Idle", avatar_state="idle")
