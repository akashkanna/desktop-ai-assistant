import sys
import os
import threading
import time
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import voice.text_to_speech as tts_module


class FakeEngine:
    def __init__(self):
        self.properties = {}
        self.last_text = None
        self.stopped = False

    def setProperty(self, name, value):
        self.properties[name] = value

    def say(self, text):
        self.last_text = text

    def runAndWait(self):
        # Simulate a short blocking speech call.
        for _ in range(10):
            if self.stopped:
                return
            time.sleep(0.01)

    def stop(self):
        self.stopped = True


def test_tts_queue_serializes_speech(monkeypatch):
    monkeypatch.setattr(tts_module, "pyttsx3", type("m", (), {"init": lambda self=None: FakeEngine()}))

    tts = tts_module.TextToSpeech()
    order = []
    done1 = threading.Event()
    done2 = threading.Event()

    def done_one():
        order.append("first")
        done1.set()

    def done_two():
        order.append("second")
        done2.set()

    tts.speak("first message", on_done=done_one)
    tts.speak("second message", on_done=done_two)

    assert done1.wait(timeout=2.0), "First speech did not finish"
    assert done2.wait(timeout=2.0), "Second speech did not finish"
    assert order == ["first", "second"]
    assert not tts.speaking
    tts.shutdown()


def test_tts_interrupt_clears_queue(monkeypatch):
    monkeypatch.setattr(tts_module, "pyttsx3", type("m", (), {"init": lambda self=None: FakeEngine()}))

    tts = tts_module.TextToSpeech()
    done = threading.Event()

    def done_cb():
        done.set()

    tts.speak("will be interrupted", on_done=done_cb)
    time.sleep(0.05)
    tts.interrupt()
    assert done.wait(timeout=2.0)
    assert not tts.speaking
    tts.shutdown()
