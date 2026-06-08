"""
Speech-to-Text — SpeechRecognition with interruptible listening.
Uses short poll timeouts so stop_listening() takes effect quickly.
"""
import time
import threading
import speech_recognition as sr
from logger_config import setup_logger

logger = setup_logger("speech_to_text")

POLL_TIMEOUT_SEC = 0.35


class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self._abort_event = threading.Event()
        try:
            with sr.Microphone() as src:
                logger.info("Calibrating ambient noise…")
                self.recognizer.adjust_for_ambient_noise(src, duration=1.5)
            logger.info(f"Energy threshold set to {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            logger.warning(f"Noise calibration failed: {e}")

        self.recognizer.energy_threshold = max(
            self.recognizer.energy_threshold, 350
        )
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def abort_listen(self):
        """Signal the current listen() call to return immediately."""
        self._abort_event.set()

    def listen(
        self,
        timeout: float = 8,
        phrase_time_limit: int = 12,
        should_continue=None,
    ) -> str:
        """
        Listen for speech. Returns transcribed text or empty string.
        should_continue: callable; return False to abort (mic stop).
        """
        if should_continue and not should_continue():
            return ""

        self._abort_event.clear()
        deadline = time.time() + timeout if timeout else None

        while True:
            if self._abort_event.is_set():
                logger.info("Listen aborted by request.")
                return ""
            if should_continue and not should_continue():
                logger.info("Listen aborted — assistant not listening.")
                return ""

            chunk_timeout = POLL_TIMEOUT_SEC
            if deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return ""
                chunk_timeout = min(chunk_timeout, remaining)

            try:
                with sr.Microphone() as source:
                    logger.debug("Listening (poll)…")
                    audio = self.recognizer.listen(
                        source,
                        timeout=chunk_timeout,
                        phrase_time_limit=phrase_time_limit,
                    )

                if self._abort_event.is_set() or (should_continue and not should_continue()):
                    return ""

                logger.info("Recognizing…")
                text = self.recognizer.recognize_google(audio, language="en-IN")
                logger.info(f"Heard: {text!r}")
                return text.strip()

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                logger.debug("Unintelligible audio.")
                return ""
            except sr.RequestError as e:
                logger.error(f"Google STT request error: {e}")
                time.sleep(0.5)
                return ""
            except Exception as e:
                logger.error(f"STT error: {e}")
                time.sleep(0.5)
                return ""
