"""Real-time microphone analyzer for live UI waveform visualization."""

import threading
from collections import deque

from PySide6.QtCore import QObject, Signal

from logger_config import setup_logger

logger = setup_logger("microphone_monitor")

try:
    import numpy as np
    import sounddevice as sd
except Exception as exc:
    np = None
    sd = None
    logger.warning(f"Audio monitor disabled: {exc}")


class MicrophoneMonitor(QObject):
    levels_updated = Signal(list, float, float, float)
    status_updated = Signal(str)

    def __init__(self, bar_count: int = 20, sample_rate: int = 16000, block_size: int = 1024,
                 noise_threshold: float = 0.008):
        super().__init__()
        self.bar_count = bar_count
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.noise_threshold = noise_threshold
        self._stream = None
        self._stream_lock = threading.Lock()
        self._band_levels = [0.0] * self.bar_count
        self._active = False
        self._status = "Idle"
        self._smoothing = 0.22
        self._decay = 0.80
        self._last_status = "Idle"

    def _build_bands(self, samples):
        if np is None or samples.size == 0:
            return [0.0] * self.bar_count

        window = samples * np.hanning(samples.shape[0])
        spectrum = np.abs(np.fft.rfft(window, n=samples.shape[0]))
        if spectrum.size == 0:
            return [0.0] * self.bar_count

        spectrum = spectrum / np.max(spectrum, initial=1.0)
        total_bins = spectrum.shape[0]
        band_edges = np.linspace(1, total_bins, self.bar_count + 1, dtype=int)
        band_levels = np.zeros(self.bar_count, dtype=float)

        for i in range(self.bar_count):
            start, end = band_edges[i], band_edges[i + 1]
            if end <= start or start >= total_bins:
                band_levels[i] = 0.0
            else:
                band = spectrum[start:end]
                band_levels[i] = float(np.sqrt(np.mean(np.square(band))))

        band_levels = np.clip(np.log1p(band_levels * 12.0) / np.log1p(12.0), 0.0, 1.0)
        return band_levels.tolist()

    def _audio_callback(self, indata, frames, time_info, status):
        if status and self._status != "Error":
            logger.debug(f"Microphone callback status: {status}")

        if np is None:
            return

        samples = np.asarray(indata, dtype=np.float32)
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)

        rms = float(np.sqrt(np.mean(np.square(samples), dtype=np.float64)))
        peak = float(np.max(np.abs(samples)))
        filtered = rms if rms >= self.noise_threshold else 0.0
        normalized = float(min(max((filtered - self.noise_threshold) * 11.5, 0.0), 1.0))
        levels = self._build_bands(samples) if filtered > 0 else [0.0] * self.bar_count

        with self._stream_lock:
            for i, target in enumerate(levels):
                value = float(max(self._band_levels[i] * self._decay, self._band_levels[i] + (target - self._band_levels[i]) * self._smoothing))
                self._band_levels[i] = max(0.0, min(1.0, value))

            level_pct = normalized * 100.0
            self._status = "Listening" if self._active else "Idle"
            self.levels_updated.emit(list(self._band_levels), rms, peak, level_pct)
            if self._status != self._last_status:
                self._last_status = self._status
                self.status_updated.emit(self._status)

    def start(self):
        if self._active:
            return

        if sd is None or np is None:
            self._status = "Mic unavailable"
            self.status_updated.emit(self._status)
            logger.warning("Cannot start microphone monitor because numpy or sounddevice is not installed.")
            return

        try:
            self._stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._active = True
            self._status = "Listening"
            self._last_status = self._status
            self.status_updated.emit(self._status)
        except Exception as exc:
            self._stream = None
            self._active = False
            self._status = "Mic unavailable"
            self.status_updated.emit(self._status)
            logger.warning(f"Failed to start microphone monitor: {exc}")

    def stop(self):
        if not self._active:
            self._status = "Idle"
            self.status_updated.emit(self._status)
            return

        with self._stream_lock:
            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
            except Exception as exc:
                logger.debug(f"Error stopping microphone stream: {exc}")
            finally:
                self._stream = None
                self._active = False
                self._band_levels = [0.0] * self.bar_count
                self._status = "Idle"
                self._last_status = self._status
                self.status_updated.emit(self._status)
                self.levels_updated.emit(self._band_levels, 0.0, 0.0, 0.0)

    @property
    def is_active(self) -> bool:
        return self._active
