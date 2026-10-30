import numpy as np
from config.settings import settings

class VoiceActivityDetector:
    def __init__(self):
        self.model = None
        self.get_speech_timestamps = None
        self._init_vad()

    def _init_vad(self):
        try:
            import torch
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=True
            )
            self.get_speech_timestamps = utils[0]
        except Exception:
            self.model = None

    def calculate_energy(self, audio_chunk: bytes) -> float:
        """Computes Root-Mean-Square (RMS) energy of 16-bit PCM audio."""
        if not audio_chunk:
            return 0.0
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
            if len(audio_np) == 0:
                return 0.0
            return float(np.sqrt(np.mean(audio_np.astype(np.float64)**2)))
        except Exception:
            return 0.0

    def is_speech(self, audio_chunk: bytes, threshold: float = 1000.0) -> bool:
        """Returns True if sound in chunk exceeds the calibrated speech threshold."""
        if not audio_chunk:
            return False

        energy = self.calculate_energy(audio_chunk)
        if self.model is None:
            return energy > threshold

        try:
            import torch
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio_np)
            speech_prob = self.model(audio_tensor, settings.SAMPLE_RATE).item()
            # Combine neural VAD probability with energy gate
            return speech_prob > 0.5 and energy > (threshold * 0.6)
        except Exception:
            return energy > threshold

vad_engine = VoiceActivityDetector()