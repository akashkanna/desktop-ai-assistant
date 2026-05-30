"""
Browser actions.
"""
import webbrowser
import json
from logger_config import setup_logger

logger = setup_logger("browser_actions")

class BrowserActions:
    def __init__(self, config_path: str = "config/app_paths.json"):
        self.websites = {}
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                self.websites = data.get("websites", {})
        except Exception as e:
            logger.error(f"Failed to load websites: {e}")

    def open_website(self, site_name: str) -> str:
        site_name_lower = site_name.lower()
        url = self.websites.get(site_name_lower)
        
        if not url:
            # Assume it's a domain if it has a dot, else search Google
            if "." in site_name_lower:
                url = f"https://{site_name_lower}"
            else:
                # Basic fallback
                url = f"https://www.google.com/search?q={site_name}"
        
        try:
            webbrowser.open(url)
            return f"Opening {site_name}."
        except Exception as e:
            logger.error(f"Failed to open website {site_name}: {e}")
            return f"I couldn't open {site_name}."
