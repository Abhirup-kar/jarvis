import io
import wave
from typing import Optional
from config.settings import settings

class SpeechToText:
    def __init__(self, model_size="base.en"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception:
                self._model = None
        return self._model

    def pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int = None) -> bytes:
        rate = sample_rate or settings.SAMPLE_RATE
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(rate)
            wf.writeframes(pcm_bytes)
        return wav_buf.getvalue()

    def transcribe_wav_bytes(self, audio_data: bytes) -> str:
        model = self._get_model()
        if model is None:
            return ""

        try:
            with io.BytesIO(audio_data) as audio_file:
                segments, _ = model.transcribe(audio_file, beam_size=2)
                return " ".join([segment.text for segment in segments]).strip()
        except Exception:
            return ""

    def transcribe_pcm(self, pcm_bytes: bytes) -> str:
        if not pcm_bytes:
            return ""
        wav_bytes = self.pcm_to_wav(pcm_bytes)
        return self.transcribe_wav_bytes(wav_bytes)

stt_engine = SpeechToText()