"""Placeholder hooks for external AI and automation providers."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IntegrationStatus:
    name: str
    connected: bool = False
    model: str = "Not configured"
    description: str = ""


class IntegrationRegistry:
    """Central registry of integration placeholders for the UI."""

    DEFAULTS: List[IntegrationStatus] = [
        IntegrationStatus("OpenAI API", False, "—", "GPT models via API key"),
        IntegrationStatus("Gemini API", False, "—", "Google Gemini multimodal"),
        IntegrationStatus("Ollama", False, "—", "Local LLM runtime"),
        IntegrationStatus("Whisper", True, "Google STT", "Speech-to-text engine"),
        IntegrationStatus("MediaPipe", True, "Hands", "Gesture recognition"),
        IntegrationStatus("MongoDB Memory", False, "JSON fallback", "Long-term memory store"),
        IntegrationStatus("pyttsx3 TTS", True, "SAPI", "Text-to-speech output"),
        IntegrationStatus("Workflow Engine", True, "Active", "Automation sequences"),
    ]

    def __init__(self):
        self._integrations: Dict[str, IntegrationStatus] = {
            i.name: i for i in self.DEFAULTS
        }

    def all(self) -> List[IntegrationStatus]:
        return list(self._integrations.values())

    def set_connected(self, name: str, connected: bool, model: str = ""):
        if name in self._integrations:
            self._integrations[name].connected = connected
            if model:
                self._integrations[name].model = model

    def primary_model_label(self) -> str:
        for key in ("Ollama", "OpenAI API", "Gemini API"):
            item = self._integrations.get(key)
            if item and item.connected:
                return f"{key}: {item.model}"
        return "Offline Intent Parser"
