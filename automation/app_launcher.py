"""
App Launcher automation.
"""
import os
import subprocess
import json
from pathlib import Path
from core.command_normalizer import resolve_app_name
from logger_config import setup_logger

logger = setup_logger("app_launcher")

# Windows-friendly fallbacks when app_paths.json has no entry
WINDOWS_APP_FALLBACKS = {
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "code": "code",
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "explorer": "explorer",
    "cmd": "cmd",
    "wt": "wt",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "teams": "teams",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "vscode": "code",
}


class AppLauncher:
    def __init__(self, config_path: str = "config/app_paths.json"):
        self.app_paths = {}
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                self.app_paths = {k.lower(): v for k, v in data.get("applications", {}).items()}
        except Exception as e:
            logger.error(f"Failed to load app paths: {e}")

    def open_application(self, app_name: str) -> str:
        display = (app_name or "").strip() or "application"
        canonical = resolve_app_name(app_name)
        if not canonical:
            return None

        app_name_lower = canonical.lower()

        if app_name_lower in self.app_paths:
            path = os.path.expandvars(self.app_paths[app_name_lower])
            if path.startswith("http"):
                import webbrowser
                webbrowser.open(path)
                return f"Opening {display}."
            try:
                subprocess.Popen([path], shell=False)
                return f"Opening {display}."
            except Exception as e:
                logger.error(f"Error opening {canonical} via Popen: {e}")

        fallback = WINDOWS_APP_FALLBACKS.get(app_name_lower, app_name_lower)
        try:
            if "setting" in app_name_lower:
                os.startfile("ms-settings:")
                return "Opening settings."
            elif "recycle bin" in app_name_lower:
                os.startfile("shell:RecycleBinFolder")
                return "Opening Recycle Bin."
            elif "camera" in app_name_lower:
                os.startfile("microsoft.windows.camera:")
                return "Opening camera."
            elif "this pc" in app_name_lower or "my computer" in app_name_lower:
                os.startfile("explorer.exe")
                return "Opening This PC."
            elif app_name_lower in ("terminal", "command", "cmd"):
                os.startfile("cmd.exe")
                return "Opening terminal."

            os.startfile(fallback)
            return f"Opening {display}."
        except Exception as exc:
            logger.error(f"Fallback launch failed for {canonical}: {exc}")
            return None
