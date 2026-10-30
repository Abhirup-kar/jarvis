import numpy as np
import asyncio
from config.settings import settings
from core.event_bus import bus
from core.state import state_manager, SystemState

class WakeWordEngine:
    def __init__(self, wake_word=None):
        self.target_word = wake_word or settings.WAKE_WORD
        self.model = None
        self.strategy = "none"
        self.idle_voice_counter = 0
        self._init_model()

    def _init_model(self):
        try:
            import openwakeword
            from openwakeword.model import Model
            openwakeword.utils.download_models()
            self.model = Model(wakeword_models=[self.target_word], inference_framework="onnx")
            self.strategy = "openwakeword"
            print(f"[WAKE WORD] OpenWakeWord model initialized for '{self.target_word}'.")
            return
        except Exception as e:
            self.model = None
            self.strategy = "vad_fallback"
            print(f"[WAKE WORD] OpenWakeWord unavailable ({e}). Using automatic VAD/voice detection fallback.")

    async def process_audio_chunk(self, audio_bytes: bytes) -> bool:
        if state_manager.current != SystemState.IDLE:
            self.idle_voice_counter = 0
            return False

        if not audio_bytes:
            return False

        # Strategy 1: OpenWakeWord Model
        if self.strategy == "openwakeword" and self.model is not None:
            try:
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
                prediction = self.model.predict(audio_np)
                
                score = prediction.get(self.target_word, 0)
                if score > 0.45:
                    print(f"\n[WAKE WORD] 🎯 Detected wake word '{self.target_word}' (score: {score:.2f})")
                    await state_manager.set_state(SystemState.LISTENING)
                    await bus.publish("wake_word_detected", {"word": self.target_word, "score": score})
                    self.model.reset()
                    return True
            except Exception:
                pass

        # Strategy 2: Debounced VAD / Sound Threshold Trigger Fallback
        elif self.strategy == "vad_fallback":
            try:
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
                energy = float(np.sqrt(np.mean(audio_np.astype(np.float64)**2)))
                if energy > 1400:  # Confident speech volume
                    self.idle_voice_counter += 1
                    # Require at least 2 consecutive frames (~128ms) to prevent single-click false triggers
                    if self.idle_voice_counter >= 2:
                        self.idle_voice_counter = 0
                        print(f"\n[VOICE] 🎙️  Voice detected (energy: {energy:.0f}). Listening for command...")
                        await state_manager.set_state(SystemState.LISTENING)
                        await bus.publish("wake_word_detected", {"word": "voice_detected", "energy": energy})
                        return True
                else:
                    self.idle_voice_counter = 0
            except Exception:
                self.idle_voice_counter = 0

        return False

wake_engine = WakeWordEngine()