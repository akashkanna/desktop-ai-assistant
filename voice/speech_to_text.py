"""
Speech-to-Text — SpeechRecognition + ambient noise calibration.
Creates a fresh Microphone() per call to avoid context-manager lock bug.
"""
import time
import speech_recognition as sr
from logger_config import setup_logger

logger = setup_logger("speech_to_text")


class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Calibrate ambient noise once on startup
        try:
            with sr.Microphone() as src:
                logger.info("Calibrating ambient noise…")
                self.recognizer.adjust_for_ambient_noise(src, duration=1.5)
            logger.info(f"Energy threshold set to {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            logger.warning(f"Noise calibration failed: {e}")

        # Raise threshold slightly to filter background chatter
        self.recognizer.energy_threshold = max(
            self.recognizer.energy_threshold, 350
        )
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # shorter pause = faster response

    def listen(self, timeout=5, phrase_time_limit=12) -> str:
        """
        Blocks until speech is detected or timeout elapses.
        Returns transcribed text or empty string.
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening…")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            logger.info("Recognizing…")
            text = self.recognizer.recognize_google(audio, language="en-IN")
            logger.info(f"Heard: {text!r}")
            return text.strip()

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            logger.debug("Unintelligible audio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Google STT request error: {e}")
            time.sleep(1)
            return ""
        except Exception as e:
            logger.error(f"STT error: {e}")
            time.sleep(1)
            return ""
