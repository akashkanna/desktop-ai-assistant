"""
App Launcher automation.
"""
import os
import subprocess
import json
from pathlib import Path
from logger_config import setup_logger

logger = setup_logger("app_launcher")

class AppLauncher:
    def __init__(self, config_path: str = "config/app_paths.json"):
        self.app_paths = {}
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                self.app_paths = data.get("applications", {})
        except Exception as e:
            logger.error(f"Failed to load app paths: {e}")

    def open_application(self, app_name: str) -> str:
        app_name_lower = app_name.lower()
        if app_name_lower in self.app_paths:
            path = os.path.expandvars(self.app_paths[app_name_lower])
            if path.startswith("http"):
                import webbrowser
                webbrowser.open(path)
                return f"Opening {app_name}."
            try:
                subprocess.Popen([path], shell=False)
                return f"Opening {app_name}."
            except Exception as e:
                logger.error(f"Error opening {app_name} via Popen: {e}")
                
        # Fallback: try opening via Windows shell
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
            elif "terminal" in app_name_lower or "command" in app_name_lower or "cmd" in app_name_lower:
                os.startfile("cmd.exe")
                return "Opening terminal."
                
            os.startfile(app_name_lower)
            return f"Opening {app_name}."
        except Exception:
            return None
