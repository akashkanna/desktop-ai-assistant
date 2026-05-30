"""Text-to-Speech — pyttsx3 with COM init for Windows threading + mute + callback.

Enhancements:
- Add type hints
- Provide an async `speak_async` method (awaitable) while keeping
  the legacy `speak` method for compatibility.
"""
from typing import Optional, Callable
import threading
import asyncio
import concurrent.futures
import pyttsx3
from logger_config import setup_logger

logger = setup_logger("text_to_speech")


class TextToSpeech:
    def __init__(self) -> None:
        self.is_muted: bool = False
        self._voice_id: Optional[str] = None
        # Single-thread executor for blocking TTS calls when used async
        self._executor: concurrent.futures.ThreadPoolExecutor = (
            concurrent.futures.ThreadPoolExecutor(max_workers=1)
        )

        # Test init and pick a default voice id if available
        try:
            eng = pyttsx3.init()
            voices = eng.getProperty("voices")
            # Pick a slightly deeper male voice (index 0) or female (1)
            self._voice_id = voices[0].id if voices else None
            eng.stop()
            logger.info("TTS ready.")
        except Exception as e:
            logger.error(f"TTS init error: {e}")
            self._voice_id = None

    def _blocking_speak(self, text: str) -> None:
        """Blocking pyttsx3 speak call. Safe to run in a worker thread."""
        try:
            import pythoncom

            pythoncom.CoInitialize()
        except Exception:
            # Not on Windows or COM already initialized
            pass

        try:
            eng = pyttsx3.init()
            eng.setProperty("rate", 170)
            eng.setProperty("volume", 1.0)
            if self._voice_id:
                eng.setProperty("voice", self._voice_id)
            eng.say(text)
            eng.runAndWait()
        except Exception as e:
            logger.error(f"TTS speak error: {e}")

    def speak(self, text: str, on_done: Optional[Callable[[], None]] = None) -> None:
        """Speak text in a background thread (compatibility wrapper).

        Calls ``on_done()`` when finished.
        """
        if self.is_muted:
            if on_done:
                on_done()
            return

        def _run_and_callback() -> None:
            try:
                self._blocking_speak(text)
            finally:
                if on_done:
                    on_done()

        threading.Thread(target=_run_and_callback, daemon=True).start()

    async def speak_async(self, text: str, on_done: Optional[Callable[[], None]] = None) -> None:
        """Async/awaitable speak. Runs the blocking engine in an executor.

        Example:
            await tts.speak_async("Hello world")
        """
        if self.is_muted:
            if on_done:
                on_done()
            return

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._executor, self._blocking_speak, text)
        except Exception as e:
            logger.error(f"TTS async speak error: {e}")
        finally:
            if on_done:
                on_done()

    def shutdown(self) -> None:
        """Clean up resources used by TTS (executor)."""
        try:
            self._executor.shutdown(wait=False)
        except Exception:
            pass
