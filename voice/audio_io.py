import asyncio
from typing import Optional, Callable, Any
from config.settings import settings
from core.event_bus import bus

class AudioIO:
    def __init__(self):
        self.backend = None  # 'pyaudio', 'sounddevice', or None
        self._pyaudio_obj = None
        self._pa_stream = None
        self._sd_stream = None
        self.is_recording = False
        self._error_message = None

    def initialize(self) -> bool:
        """Attempts to initialize either PyAudio or SoundDevice."""
        self._error_message = None

        # 1. Try PyAudio
        try:
            import pyaudio
            self._pyaudio_obj = pyaudio.PyAudio()
            # Test opening input stream
            test_stream = self._pyaudio_obj.open(
                rate=settings.SAMPLE_RATE,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=settings.CHUNK_SIZE
            )
            test_stream.close()
            self.backend = 'pyaudio'
            print("[AUDIO] PyAudio input stream initialized successfully.")
            return True
        except Exception as pa_err:
            self._error_message = f"PyAudio error: {pa_err}"

        # 2. Try SoundDevice fallback
        try:
            import sounddevice as sd
            # Test default input device
            sd.check_input_settings(samplerate=settings.SAMPLE_RATE, channels=1, dtype='int16')
            self.backend = 'sounddevice'
            print("[AUDIO] SoundDevice input stream initialized successfully.")
            return True
        except Exception as sd_err:
            self._error_message = f"Audio capture unavailable: {self._error_message} | SoundDevice error: {sd_err}"

        print(f"[AUDIO WARN] {self._error_message}")
        print("[AUDIO TIP] Install system audio drivers (`sudo apt install portaudio19-dev`) or use the Web HUD.")
        return False

    def start_stream(self) -> bool:
        if not self.backend:
            if not self.initialize():
                return False

        try:
            if self.backend == 'pyaudio':
                import pyaudio
                self._pa_stream = self._pyaudio_obj.open(
                    rate=settings.SAMPLE_RATE,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=settings.CHUNK_SIZE
                )
                self.is_recording = True
                return True
            elif self.backend == 'sounddevice':
                import sounddevice as sd
                self.is_recording = True
                return True
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to start audio recording stream: {e}")
            self.is_recording = False
            return False

    def stop_stream(self):
        self.is_recording = False
        if self._pa_stream:
            try:
                self._pa_stream.stop_stream()
                self._pa_stream.close()
            except Exception:
                pass
            self._pa_stream = None
        if self._pyaudio_obj:
            try:
                self._pyaudio_obj.terminate()
            except Exception:
                pass
            self._pyaudio_obj = None

    async def capture_continuous(self, callback: Callable[[bytes], Any]):
        """Continuously reads audio chunks and feeds them to the callback."""
        if not self.is_recording:
            started = self.start_stream()
            if not started:
                # Keep alive in idle sleep mode if no mic hardware exists
                while True:
                    await asyncio.sleep(1.0)

        if self.backend == 'pyaudio' and self._pa_stream:
            while self.is_recording and self._pa_stream:
                try:
                    data = await asyncio.to_thread(
                        self._pa_stream.read, 
                        settings.CHUNK_SIZE, 
                        exception_on_overflow=False
                    )
                    await callback(data)
                except Exception:
                    await asyncio.sleep(0.05)

        elif self.backend == 'sounddevice':
            import sounddevice as sd
            import numpy as np
            loop = asyncio.get_running_loop()

            def _sd_callback(indata, frames, time, status):
                if self.is_recording:
                    pcm_bytes = indata.tobytes()
                    asyncio.run_coroutine_threadsafe(callback(pcm_bytes), loop)

            with sd.RawInputStream(
                samplerate=settings.SAMPLE_RATE,
                blocksize=settings.CHUNK_SIZE,
                channels=1,
                dtype='int16',
                callback=_sd_callback
            ):
                while self.is_recording:
                    await asyncio.sleep(0.1)

audio_io = AudioIO()