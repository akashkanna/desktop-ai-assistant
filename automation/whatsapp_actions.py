"""
WhatsApp actions (Basic Web implementation).
"""
import webbrowser
import urllib.parse
from logger_config import setup_logger

logger = setup_logger("whatsapp_actions")

class WhatsAppActions:
    def send_message(self, contact: str, message: str) -> str:
        """
        Drafts a message on WhatsApp Web using the URL scheme.
        For MVP, it opens the browser. 
        Note: The URL scheme doesn't automatically search by contact name well without API,
        but we can try a basic implementation or just instruct the user.
        A full automation would use Selenium/Playwright.
        """
        encoded_msg = urllib.parse.quote(message)
        # Without an exact phone number, WA Web URL api is limited.
        # MVP: Just open WhatsApp web and instruct.
        url = f"https://web.whatsapp.com/+919944737206"
        webbrowser.open(url)
        
        # In a complete implementation, this would use PyAutoGUI to search the contact
        # and type the message after waiting for the page to load.
        
        return f"I have opened WhatsApp. Please select {contact} to send the message: {message}"
