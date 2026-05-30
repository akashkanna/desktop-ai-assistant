"""Base classes and helpers for Jarvis plugins."""

from abc import ABC, abstractmethod

class PluginBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def actions(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def voice_commands(self) -> list[str]:
        raise NotImplementedError
