"""
Speech-to-Text — SpeechRecognition with interruptible listening.
Uses short poll timeouts so stop_listening() takes effect quickly.
The active microphone source is tracked so it can be forcefully
closed from another thread when abort_listen() is called.
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
        self._source_lock = threading.Lock()
        self._active_source = None          # tracks the open Microphone

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

    # ── abort / force-close ─────────────────────────────────────────

    def abort_listen(self):
        """Signal the current listen() call to return immediately
        and close any microphone stream that is currently open."""
        self._abort_event.set()
        self._close_active_source()

    def force_stop(self):
        """Hard stop — sets the abort flag and tears down the mic."""
        self._abort_event.set()
        self._close_active_source()
        logger.info("SpeechToText force-stopped.")

    def _close_active_source(self):
        """Safely close the active microphone source if one is open."""
        with self._source_lock:
            src = self._active_source
            if src is not None:
                try:
                    src.__exit__(None, None, None)
                except Exception:
                    pass
                self._active_source = None

    # ── main listen method ──────────────────────────────────────────

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
        if self._abort_event.is_set():
            return ""
        if should_continue and not should_continue():
            return ""

        self._abort_event.clear()
        deadline = time.time() + timeout if timeout else None

        while True:
            # ── fast bail-out checks ─────────────────────────────
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
                # Check abort *before* opening the microphone
                if self._abort_event.is_set():
                    return ""

                source = sr.Microphone()
                source.__enter__()

                with self._source_lock:
                    if self._abort_event.is_set():
                        # Abort was called between creating and registering
                        try:
                            source.__exit__(None, None, None)
                        except Exception:
                            pass
                        return ""
                    self._active_source = source

                try:
                    logger.debug("Listening (poll)…")
                    audio = self.recognizer.listen(
                        source,
                        timeout=chunk_timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
                finally:
                    # Always close the mic and clear the reference
                    with self._source_lock:
                        self._active_source = None
                    try:
                        source.__exit__(None, None, None)
                    except Exception:
                        pass

                # Check abort *after* listening
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
                if self._abort_event.is_set():
                    # Expected — mic was force-closed during listen
                    logger.debug("Listen interrupted by abort.")
                    return ""
                logger.error(f"STT error: {e}")
                time.sleep(0.5)
                return ""
