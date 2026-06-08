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

try:
    import keyboard
except ImportError:
    keyboard = None

logger = setup_logger("task_router")

# Centralized mapping of user-friendly intent names to keyboard key combinations.
# Extend this dict when adding new shortcut intents.
SHORTCUTS = {
    # Clipboard
    "copy": "ctrl+c",
    "paste": "ctrl+v",
    "cut": "ctrl+x",
    "clipboard_history": "windows+v",

    # Editing
    "undo": "ctrl+z",
    "redo": "ctrl+y",
    "select_all": "ctrl+a",
    "save": "ctrl+s",
    "save_as": "ctrl+shift+s",
    "find": "ctrl+f",
    "replace": "ctrl+h",
    "print": "ctrl+p",
    "new_file": "ctrl+n",
    "open_file": "ctrl+o",

    # Browser Tabs
    "new_tab": "ctrl+t",
    "close_tab": "ctrl+w",
    "reopen_tab": "ctrl+shift+t",
    "next_tab": "ctrl+tab",
    "previous_tab": "ctrl+shift+tab",
    "refresh": "f5",
    "hard_refresh": "ctrl+f5",
    "address_bar": "ctrl+l",
    "downloads": "ctrl+j",
    "history": "ctrl+h",
    "bookmark_page": "ctrl+d",
    "incognito": "ctrl+shift+n",

    # Window Management
    "switch_window": "alt+tab",
    "previous_window": "alt+shift+tab",
    "close_window": "alt+f4",
    "minimize_window": "windows+down",
    "maximize_window": "windows+up",

    # Windows System
    "show_desktop": "windows+d",
    "minimize_all": "windows+m",
    "restore_windows": "windows+shift+m",
    "open_explorer": "windows+e",
    "open_settings": "windows+i",
    "lock_pc": "windows+l",
    "run_dialog": "windows+r",
    "search_windows": "windows+s",
    "quick_link_menu": "windows+x",
    "notification_center": "windows+a",
    "widgets": "windows+w",
    "game_bar": "windows+g",
    "project_screen": "windows+p",
    "emoji_panel": "windows+.",
    "task_view": "windows+tab",
    "screenshot": "windows+shift+s",

    # Window Snap
    "snap_left": "windows+left",
    "snap_right": "windows+right",
    "snap_up": "windows+up",
    "snap_down": "windows+down",

    # Navigation
    "scroll_top": "ctrl+home",
    "scroll_bottom": "ctrl+end",
    "page_up": "pageup",
    "page_down": "pagedown",
    "home": "home",
    "end": "end",

    # Virtual Desktops
    "new_desktop": "windows+ctrl+d",
    "next_desktop": "windows+ctrl+right",
    "previous_desktop": "windows+ctrl+left",
    "close_desktop": "windows+ctrl+f4",

    # Task Manager
    "task_manager": "ctrl+shift+esc",

    # Function keys
    "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4", "f5": "f5",
    "f6": "f6", "f7": "f7", "f8": "f8", "f9": "f9", "f10": "f10",
    "f11": "f11", "fullscreen": "f11", "f12": "f12",

    # Direct windows keys (aliases)
    **{f"win_{c}": f"windows+{c}" for c in list('abcdefghijklmnopqrstuvwxyz')}
}


class TaskRouter:
    def __init__(self, settings=None, context_manager=None):
        self.settings = settings or {}
        self.context_manager = context_manager
        self.app_launcher = AppLauncher()
        self.browser = BrowserActions()
        self.whatsapp = WhatsAppActions()
        self.clarification_manager = None
        self._last_response = ""
        self._parser = IntentParser(self.context_manager, self.settings)
        self.on_clarification_needed = lambda question, intent: None
        self.on_confirmation_needed = lambda intent, message: None

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
        if intent == "unknown":
            shortcut_fallback = self._handle_unknown_shortcut(entities)
            if shortcut_fallback is not None:
                return shortcut_fallback

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

        elif intent in SHORTCUTS:
            return self._perform_shortcut_intent(intent)

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

    def _get_whatsapp(self):
        return self.whatsapp

    def _normalize_shortcut_raw(self, raw: str) -> str:
        raw = raw.strip().lower()
        raw = re.sub(r"\b(copy|cut|paste)(?:\s+\1)+\b", r"\1", raw)
        return raw

    def _handle_unknown_shortcut(self, entities: dict) -> str | None:
        raw = entities.get("raw", "")
        normalized = self._normalize_shortcut_raw(raw)
        if normalized in ("copy", "cut", "paste"):
            return self._perform_shortcut_intent(normalized)
        if normalized in ("refresh", "refresh refresh", "reload", "hard refresh"):
            return self._perform_shortcut_intent("refresh")
        return None

    def _perform_shortcut_intent(self, intent: str) -> str:
        """Map simple keyboard intents to system hotkeys and execute them."""
        if keyboard is None:
            return (
                "Keyboard automation is unavailable. "
                "Install the keyboard package to enable shortcuts."
            )

        intent_key = intent.lower()
        key_combo = SHORTCUTS.get(intent_key)
        if not key_combo:
            return f"I don't have a keyboard shortcut mapped for '{intent}'."

        try:
            keyboard.press_and_release(key_combo)
            return f"Executed shortcut for {intent.title()}."
        except Exception as exc:
            logger.error(f"Failed to execute shortcut for {intent}: {exc}")
            return f"I could not perform {intent} right now."

    def route(self, intent_data: dict):
        """Route a parsed intent dict through clarification, confirmation, or execution."""
        intent = intent_data.get("intent")
        confidence = intent_data.get("confidence", 1.0)
        entities = intent_data.get("entities", {})
        missing = intent_data.get("missing_fields", [])
        requires_confirmation = intent_data.get("requires_confirmation", False)
        response = intent_data.get("response", "")

        if intent == "unknown":
            shortcut_fallback = self._handle_unknown_shortcut(entities)
            if shortcut_fallback is not None:
                return True, shortcut_fallback

        if intent == "cancel_task":
            if self.context_manager and hasattr(self.context_manager, "clear_pending_confirmation"):
                self.context_manager.clear_pending_confirmation()
            elif self.context_manager and hasattr(self.context_manager, "clear_pending"):
                self.context_manager.clear_pending()
            return True, response or "Cancelled."

        threshold = self.settings.get("confidence_threshold", 0.65)
        if confidence < threshold or missing:
            if not self.clarification_manager:
                from core.clarification_manager import ClarificationManager
                self.clarification_manager = ClarificationManager(threshold)
            question = self.clarification_manager.get_question(
                ParsedIntent(intent, confidence, entities, requires_confirmation, missing)
            )
            self.on_clarification_needed(question, intent_data)
            return False, question

        if requires_confirmation:
            if self.context_manager:
                self.context_manager.set_pending_confirmation(intent_data)
            self.on_confirmation_needed(intent, response)
            return False, response or f"Please confirm {intent}."

        return True, self._dispatch(intent, entities, ParsedIntent(intent, confidence, entities, requires_confirmation, missing))

    def _looks_like_question(self, text: str) -> bool:
        if not text or len(text.split()) < 2:
            return False
        q_words = ("who", "what", "where", "when", "why", "how", "which",
                   "is", "are", "does", "do", "can", "tell me about")
        return any(text.lower().startswith(w) for w in q_words)
