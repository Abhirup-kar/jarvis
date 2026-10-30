import unittest
import asyncio
import numpy as np
from core.state import state_manager, SystemState
from core.interrupt import interrupt_controller
from core.event_bus import bus
from voice.vad import vad_engine
from voice.stt import stt_engine
from voice.tts import tts_engine
from voice.wake_word import wake_engine

class TestVoice(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await state_manager.set_state(SystemState.IDLE)

    def test_vad_silence_vs_sound(self):
        # 16-bit PCM silent chunk
        silent_chunk = np.zeros(1024, dtype=np.int16).tobytes()
        self.assertFalse(vad_engine.is_speech(silent_chunk))

        # 16-bit PCM loud sine wave chunk
        t = np.linspace(0, 1, 1024)
        loud_signal = (np.sin(2 * np.pi * 440 * t) * 15000).astype(np.int16).tobytes()
        self.assertTrue(vad_engine.is_speech(loud_signal))

    def test_stt_empty_bytes(self):
        result = stt_engine.transcribe_wav_bytes(b"")
        self.assertEqual(result, "")

    async def test_interrupt_controller_barge_in(self):
        await state_manager.set_state(SystemState.SPEAKING)
        interrupted_events = []
        bus.subscribe("system_interrupted", lambda data: interrupted_events.append(data))

        await interrupt_controller.trigger_barge_in(reason="voice_detected")
        self.assertEqual(state_manager.current, SystemState.LISTENING)
        self.assertEqual(len(interrupted_events), 1)
        self.assertEqual(interrupted_events[0]["reason"], "voice_detected")

    async def test_tts_state_flow(self):
        # Speaking changes state and resets back to IDLE
        await tts_engine.speak("") # Empty text should no-op
        self.assertEqual(state_manager.current, SystemState.IDLE)

if __name__ == "__main__":
    unittest.main()

