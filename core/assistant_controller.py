"""
Assistant Controller — central brain.
Wires STT, TTS, Intent Parser, Context, Task Router, and UI signals.
"""
import threading
import time
from core.intent_parser import IntentParser
from core.context_manager import ContextManager
from core.clarification_manager import ClarificationManager
from core.predictive_engine import PredictiveEngine
from core.safety_manager import SafetyManager
from core.task_router import TaskRouter
from core.workflow_engine import WorkflowEngine
from core.task_monitor import TaskMonitor
from core.notification_manager import NotificationManager
from core.plugin_manager import PluginManager
from gesture import GestureController
from voice.microphone_monitor import MicrophoneMonitor
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
        self.predictive_engine = PredictiveEngine(self.context_manager)
        self.safety_manager = SafetyManager()
        self.task_router = TaskRouter()
        self.workflow_engine = WorkflowEngine(self.task_router, self.context_manager.ltm)
        self.task_monitor = TaskMonitor()
        self.notification_manager = NotificationManager(self.context_manager.ltm)
        self.plugin_manager = PluginManager()
        self.gesture_controller = GestureController()

        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.mic_monitor = MicrophoneMonitor(bar_count=36)

        self.is_listening = False
        self.listen_thread = None

        logger.info("AssistantController initialized.")

    # ─────────────────────────── UI helper ───────────────────────────

    def update_ui(self, status=None, user_text=None, assistant_text=None,
                  is_muted=None, avatar_state=None, refresh_ui=False):
        if self.ui_callback:
            self.ui_callback(
                status=status,
                user_text=user_text,
                assistant_text=assistant_text,
                is_muted=is_muted,
                avatar_state=avatar_state,
                refresh_ui=refresh_ui,
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

        # 3.5. Detect a saved workflow by voice trigger first
        workflow = self.workflow_engine.find_workflow_for_text(text)
        if workflow:
            result = self.workflow_engine.execute_workflow(workflow["name"])
            self.speak(result)
            return

        # 4. Handle dedicated assistant features first
        if self._handle_special_intent(parsed, text):
            return

        # 5. Clarification needed?
        if self.clarification_manager.needs_clarification(parsed):
            state = self.clarification_manager.build_clarification_state(parsed)
            self.context_manager.set_clarification(state)
            self.speak(state["question_asked"])
            return

        # 6. Safety / confirmation needed?
        if not self.safety_manager.is_safe_to_execute(parsed):
            self.context_manager.set_pending_confirmation(parsed.to_dict())
            self.speak(f"Do you want me to proceed with: {parsed.intent.replace('_', ' ')}?")
            return

        # 7. Execute
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

    def _handle_special_intent(self, parsed, original_text: str) -> bool:
        if parsed.intent == "remember_preference":
            value = parsed.entities.get("preference_value") or parsed.entities.get("raw")
            key = parsed.entities.get("preference_key") or self._guess_preference_key(value)
            if value:
                self.context_manager.ltm.set_preference(key, value)
                self.speak(f"I will remember that {value}.")
                return True
            self.speak("What should I remember?")
            return True

        if parsed.intent == "create_workflow":
            name = parsed.entities.get("workflow_name")
            definition = parsed.entities.get("workflow_definition", "")
            if not name:
                self.speak("What would you like to name this workflow?")
                return True
            steps = self._parse_workflow_steps(definition)
            if not steps:
                self.speak("Please describe the workflow steps after the workflow name.")
                return True
            self.workflow_engine.create_workflow(name, steps, trigger=name)
            self.speak(f"Workflow '{name}' is ready. Say 'run {name}' to launch it.")
            return True

        if parsed.intent == "run_workflow":
            name = parsed.entities.get("workflow_name")
            if not name:
                self.speak("Which workflow should I run?")
                return True
            result = self.workflow_engine.execute_workflow(name)
            self.speak(result)
            return True

        if parsed.intent == "list_workflows":
            workflows = self.workflow_engine.list_workflows()
            if not workflows:
                self.speak("You don't have any saved workflows yet.")
                return True
            names = ", ".join(w["name"] for w in workflows)
            self.speak(f"I found these workflows: {names}.")
            return True

        if parsed.intent == "show_notifications":
            notifications = self.notification_manager.get_unread()
            if not notifications:
                self.speak("You have no unread notifications.")
                return True
            messages = "; ".join(f"{n.title}: {n.message}" for n in notifications[:3])
            self.speak(f"Unread notifications: {messages}")
            return True

        if parsed.intent == "task_status":
            task_name = parsed.entities.get("task_name")
            tasks = [t for t in self.task_monitor.list_tasks() if task_name and task_name.lower() in t.name.lower()] if task_name else self.task_monitor.list_tasks()
            if not tasks:
                self.speak("I couldn't find any matching tasks.")
                return True
            details = "; ".join(f"{t.name} is {t.status}" for t in tasks[:3])
            self.speak(details)
            return True

        if parsed.intent == "enable_gesture_mode":
            response = self.gesture_controller.start()
            self.speak(response)
            return True

        if parsed.intent == "disable_gesture_mode":
            response = self.gesture_controller.stop()
            self.speak(response)
            return True

        if parsed.intent == "move_window_left":
            response = self.gesture_controller.move_active_window_left()
            self.speak(response)
            return True

        if parsed.intent == "move_window_right":
            response = self.gesture_controller.move_active_window_right()
            self.speak(response)
            return True

        if parsed.intent == "scroll_top":
            response = self.gesture_controller.scroll_to_top()
            self.speak(response)
            return True

        if parsed.intent == "scroll_bottom":
            response = self.gesture_controller.scroll_to_bottom()
            self.speak(response)
            return True

        return False

    def _guess_preference_key(self, value: str) -> str:
        if not value:
            return "preferred_setting"
        text = value.lower()
        if "dark" in text or "light" in text or "theme" in text:
            return "preferred_theme"
        if "volume" in text or "%" in text:
            return "preferred_volume"
        if "night" in text or "brightness" in text:
            return "night_light_enabled"
        return "preferred_setting"

    def _parse_workflow_steps(self, definition: str) -> list:
        pieces = [p.strip() for p in definition.split(",") if p.strip()]
        return [{"text": piece} for piece in pieces]

    def _execute_parsed_intent(self, parsed, original_text: str):
        if parsed.intent == "cancel":
            self.speak("Cancelled.")
            return

        if parsed.intent == "refresh_ui":
            task = self.task_monitor.create_task(parsed.intent, message=original_text)
            self.task_monitor.update_task(task.task_id, "running")
            self.update_ui(status="Refreshing…", avatar_state="thinking", refresh_ui=True)
            self.context_manager.update_after_execution(parsed, original_text)
            result = "Refreshed the dashboard."
            self.task_monitor.update_task(task.task_id, "completed", message=result)
            self.speak(result)
            return

        task = self.task_monitor.create_task(parsed.intent, message=original_text)
        self.task_monitor.update_task(task.task_id, "running")

        self.update_ui(status="Executing…", avatar_state="thinking")
        result = self.task_router.execute(parsed)
        self.context_manager.update_after_execution(parsed, original_text)

        status = "completed" if result and "error" not in result.lower() else "failed"
        self.task_monitor.update_task(task.task_id, status, message=result)

        if parsed.intent == "greeting":
            suggestion = self.predictive_engine.suggest_routine()
            if suggestion:
                result = f"{result} {suggestion}"

        self.speak(result)

    # ─────────────────────────── voice loop ──────────────────────────

    def start_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.stt._abort_event.clear()
        self.mic_monitor.start()
        self.update_ui(status="Listening…", avatar_state="listening")

        if self.listen_thread and self.listen_thread.is_alive():
            return

        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def stop_listening(self):
        was_listening = self.is_listening
        self.is_listening = False
        self.stt.abort_listen()
        self.mic_monitor.stop()
        if was_listening:
            self.update_ui(status="Idle", avatar_state="idle")
            logger.info("Voice listening stopped.")

    def _listen_loop(self):
        """Persistent loop — idle-waits when not listening, exits only on app shutdown."""
        while True:
            if not self.is_listening:
                time.sleep(0.15)
                continue

            with self.tts._audio_lock:
                text = self.stt.listen(
                    timeout=10,
                    phrase_time_limit=15,
                    should_continue=lambda: self.is_listening,
                )

            if not self.is_listening:
                continue

            if text:
                self.process_text_input(text)

    def shutdown(self):
        self.is_listening = False
        self.stt.abort_listen()
        self.stop_listening()
        try:
            self.tts.shutdown()
        except Exception as e:
            logger.warning(f"Assistant shutdown error: {e}")
