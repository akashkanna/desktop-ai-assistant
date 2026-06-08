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
import queue
import pyttsx3
from logger_config import setup_logger

logger = setup_logger("text_to_speech")


class TextToSpeech:
    def __init__(self) -> None:
        self.is_muted: bool = False
        self._voice_id: Optional[str] = None
        self._queue: queue.Queue = queue.Queue()
        self._audio_lock = threading.RLock()
        self.audio_lock = self._audio_lock
        self._current_engine = None
        self._shutdown_event = threading.Event()
        self._is_speaking = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        try:
            eng = pyttsx3.init()
            voices = eng.getProperty("voices")
            self._voice_id = voices[0].id if voices else None
            eng.stop()
            logger.info("TTS ready.")
        except Exception as e:
            logger.error(f"TTS init error: {e}")
            self._voice_id = None

    def _worker(self) -> None:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.setProperty("volume", 1.0)
            if self._voice_id:
                engine.setProperty("voice", self._voice_id)
        except Exception as e:
            logger.error(f"TTS worker init failed: {e}")
            engine = None

        while not self._shutdown_event.is_set():
            try:
                task = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if task is None:
                break

            text, on_done = task
            if self.is_muted:
                if on_done:
                    on_done()
                continue

            if engine is None:
                logger.error("TTS engine unavailable.")
                if on_done:
                    on_done()
                continue

            self._is_speaking.set()
            self._current_engine = engine
            try:
                with self._audio_lock:
                    engine.say(text)
                    engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
                try:
                    engine.stop()
                except Exception:
                    pass
            finally:
                self._current_engine = None
                self._is_speaking.clear()
                if on_done:
                    on_done()

    def speak(self, text: str, on_done: Optional[Callable[[], None]] = None) -> None:
        """Enqueue text for sequential speech output."""
        if self.is_muted:
            if on_done:
                on_done()
            return

        self._queue.put((text, on_done))

    async def speak_async(self, text: str, on_done: Optional[Callable[[], None]] = None) -> None:
        """Async/awaitable speak via the TTS worker queue."""
        if self.is_muted:
            if on_done:
                on_done()
            return

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _callback() -> None:
            if on_done:
                try:
                    on_done()
                except Exception as e:
                    logger.error(f"TTS on_done callback error: {e}")
            loop.call_soon_threadsafe(future.set_result, None)

        self._queue.put((text, _callback))
        await future

    def interrupt(self) -> None:
        """Stop current speech and clear pending TTS tasks."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        if self._current_engine is not None:
            try:
                self._current_engine.stop()
            except Exception as e:
                logger.warning(f"TTS interrupt failed: {e}")

    @property
    def speaking(self) -> bool:
        return self._is_speaking.is_set()

    def shutdown(self) -> None:
        """Clean up the TTS worker thread."""
        self._shutdown_event.set()
        self._queue.put(None)
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
