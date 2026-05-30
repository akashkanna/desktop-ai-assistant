"""
Task Router — dispatches intents to the correct automation module.
Handles compound commands like "open Chrome and search Gopal".
"""
import re
import webbrowser
from core.intent_parser import ParsedIntent, IntentParser
from automation.app_launcher import AppLauncher
from automation.browser_actions import BrowserActions
from automation.whatsapp_actions import WhatsAppActions
import automation.system_controls as sys_ctrl
from logger_config import setup_logger

logger = setup_logger("task_router")


class TaskRouter:
    def __init__(self):
        self.app_launcher  = AppLauncher()
        self.browser       = BrowserActions()
        self.whatsapp      = WhatsAppActions()
        self._last_response = ""
        self._parser = IntentParser()

    # ─────────────────────────── public ──────────────────────────────

    def execute(self, parsed: ParsedIntent) -> str:
        intent   = parsed.intent
        entities = parsed.entities
        logger.info(f"Executing intent={intent} entities={entities}")

        try:
            result = self._dispatch(intent, entities, parsed)
        except Exception as e:
            logger.error(f"Execution error for {intent}: {e}")
            result = "I encountered an error while performing that action."

        if result and intent != "repeat_last":
            self._last_response = result
        return result

    # ─────────────────────────── dispatcher ──────────────────────────

    def _dispatch(self, intent: str, entities: dict, parsed: ParsedIntent) -> str:

        # ── Applications ─────────────────────────────────────────────
        if intent == "open_application":
            raw = entities.get("application", "")
            # Compound: "open Chrome and search Gopal"
            compound = self._split_compound(raw)
            if compound:
                app_part, action_part = compound
                res = self._open_app(app_part)
                import time; time.sleep(1.5)   # let app open
                res2 = self._dispatch_text(action_part)
                return f"{res} {res2}".strip()
            return self._open_app(raw)

        elif intent == "close_application":
            app = entities.get("application", "")
            if not app or app in ("all", "everything"):
                return sys_ctrl.minimize_all_windows()
            return sys_ctrl.close_window(app)

        elif intent == "minimize_window":
            app = entities.get("application", "")
            if not app or app in ("all", "all windows", "everything", "all tabs"):
                return sys_ctrl.minimize_all_windows()
            return sys_ctrl.minimize_window(app)

        elif intent == "maximize_window":
            app = entities.get("application", "")
            return sys_ctrl.maximize_window(app or None)

        # ── Browser / Web ─────────────────────────────────────────────
        elif intent == "open_website":
            url = entities.get("website", "")
            return self.browser.open_website(url)

        elif intent == "search_web":
            query = entities.get("query", "")
            engine = entities.get("engine", "google")
            return self._web_search(query, engine)

        elif intent == "search_youtube":
            query = entities.get("query", "")
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."

        # ── WhatsApp ──────────────────────────────────────────────────
        elif intent == "send_whatsapp_message":
            return self.whatsapp.send_message(
                entities.get("contact", ""),
                entities.get("message", ""),
            )

        # ── Volume ────────────────────────────────────────────────────
        elif intent == "volume_control":
            action = entities.get("action", "set")
            level  = entities.get("level")

            if action == "increase":
                return sys_ctrl.increase_volume(level if level is not None else 10)
            elif action == "decrease":
                return sys_ctrl.decrease_volume(level if level is not None else 10)
            elif action == "mute":
                return sys_ctrl.mute_volume()
            elif action == "unmute":
                return sys_ctrl.unmute_volume()
            else:
                if level is not None:
                    return sys_ctrl.set_volume(level)
                else:
                    return "Please specify the volume level, for example 'set volume to 50 percent'."

        # ── System power ──────────────────────────────────────────────
        elif intent == "sleep_mode":
            return sys_ctrl.sleep_system()

        elif intent == "lock_screen":
            return sys_ctrl.lock_screen()

        elif intent == "shutdown":
            return sys_ctrl.shutdown_system()

        elif intent == "restart":
            return sys_ctrl.restart_system()

        elif intent == "cancel_shutdown":
            return sys_ctrl.cancel_shutdown()
            
        elif intent == "take_screenshot":
            return sys_ctrl.take_screenshot()

        # ── Conversational ────────────────────────────────────────────
        elif intent == "greeting":
            import time
            hour = int(time.strftime("%H"))
            if hour < 12:
                greet = "Good morning"
            elif hour < 17:
                greet = "Good afternoon"
            else:
                greet = "Good evening"
            return f"{greet}! I'm Jarvis. How can I help you?"

        elif intent == "ask_name":
            return "I am Jarvis, your personal AI desktop assistant."

        elif intent == "ask_time":
            import time
            return f"The current time is {time.strftime('%I:%M %p')}."

        elif intent == "ask_date":
            from datetime import datetime
            return f"Today is {datetime.now().strftime('%A, %d %B %Y')}."

        elif intent == "ask_how_are_you":
            return "I'm fully operational and ready to help! What can I do for you?"

        elif intent in ("ask_capabilities", "help"):
            try:
                import os
                readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
                if os.path.exists(readme_path):
                    os.startfile(readme_path)
                    return "I have opened my documentation file for you. It contains a complete list of my commands and rules."
            except Exception as e:
                logger.error(f"Failed to open README: {e}")
            
            return (
                "I can open and close apps, browse websites, search Google or YouTube, "
                "control your volume, power, and windows, send WhatsApp messages, "
                "and take screenshots. Check my README file for full details."
            )

        elif intent == "repeat_last":
            return self._last_response or "I have nothing to repeat yet."

        elif intent == "cancel":
            return "Operation cancelled."

        elif intent == "unknown":
            # Smart fallback: search the web for anything that looks like a question
            raw = entities.get("raw", "")
            if self._looks_like_question(raw):
                return self._web_search(raw, "google")
            return (
                "I didn't understand that. Try saying something like: "
                "'open Chrome', 'search Google for recipes', or 'what time is it'."
            )

        else:
            return f"I don't know how to handle '{intent}' yet."

    # ─────────────────────────── helpers ─────────────────────────────

    def _open_app(self, app_name: str) -> str:
        result = self.app_launcher.open_application(app_name)
        return result or f"I could not find '{app_name}' on your system."

    def _web_search(self, query: str, engine: str = "google") -> str:
        if not query:
            return "What would you like me to search for?"
        q = query.replace(" ", "+")
        if engine == "youtube":
            url = f"https://www.youtube.com/results?search_query={q}"
        elif engine == "bing":
            url = f"https://www.bing.com/search?q={q}"
        else:
            url = f"https://www.google.com/search?q={q}"
        webbrowser.open(url)
        return f"Searching for '{query}' on {engine.capitalize()}."

    def _split_compound(self, text: str):
        """Detect 'open X and search/go to/play Y' compound commands."""
        m = re.match(
            r"^(?P<app>.+?)\s+and\s+(?P<action>search|find|look\s+up|go\s+to|play|open)\s+(?P<rest>.+)$",
            text.strip(), re.IGNORECASE
        )
        if m:
            return m.group("app").strip(), f"{m.group('action')} {m.group('rest')}".strip()
        return None

    def _dispatch_text(self, text: str) -> str:
        """Re-parse a sub-command and execute it."""
        parsed = self._parser.parse(text)
        return self._dispatch(parsed.intent, parsed.entities, parsed)

    def _looks_like_question(self, text: str) -> bool:
        if not text or len(text.split()) < 2:
            return False
        q_words = ("who", "what", "where", "when", "why", "how", "which",
                   "is", "are", "does", "do", "can", "tell me about")
        return any(text.lower().startswith(w) for w in q_words)
