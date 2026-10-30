import asyncio
from typing import List
from config.settings import settings
from core.state import state_manager, SystemState
from core.agent import jarvis_agent
from core.interrupt import interrupt_controller
from voice.audio_io import audio_io
from voice.wake_word import wake_engine
from voice.vad import vad_engine
from voice.stt import stt_engine
from voice.tts import tts_engine

class ContinuousVoiceListener:
    """Continuous microphone worker with debounced Barge-in and speaker echo suppression."""

    def __init__(self):
        self.audio_buffer: List[bytes] = []
        self.is_speaking_user = False
        self.silence_frames = 0
        self.max_silence_frames = 18  # ~1.1 seconds of silence at 16000Hz/1024 chunk
        self.min_speech_frames = 4
        self.speech_frames_count = 0
        self.is_running = False
        self._processing_lock = asyncio.Lock()
        
        # Debouncing and echo suppression counters
        self.speaking_frame_count = 0
        self.barge_in_counter = 0

    async def start(self):
        """Starts the continuous microphone listening loop."""
        self.is_running = True
        print(f"[VOICE] 🎙️  Microphone stream active. Listening for '{settings.WAKE_WORD}'...")

        async def _audio_chunk_handler(chunk: bytes):
            current_state = state_manager.current

            # 1. State: IDLE -> Listen for Wake Word or Confident Voice
            if current_state == SystemState.IDLE:
                self.speaking_frame_count = 0
                self.barge_in_counter = 0
                await wake_engine.process_audio_chunk(chunk)

            # 2. State: SPEAKING or THINKING -> Robust Barge-In Detection (Echo Filtered)
            elif current_state in (SystemState.SPEAKING, SystemState.THINKING, SystemState.EXECUTING):
                self.speaking_frame_count += 1
                
                # Grace period: ignore the first 8 frames (~500ms) to prevent speaker init false-barge-in
                if self.speaking_frame_count < 8:
                    return

                # High threshold (2800) to ensure genuine human voice over ambient speaker bleed
                is_loud_speech = vad_engine.is_speech(chunk, threshold=2800.0)
                if is_loud_speech:
                    self.barge_in_counter += 1
                    # Require 5 consecutive high-energy frames (~320ms sustained speech)
                    if self.barge_in_counter >= 5:
                        self.barge_in_counter = 0
                        self.speaking_frame_count = 0
                        
                        # Trigger barge-in: kill TTS output immediately
                        await interrupt_controller.trigger_barge_in(reason="user_speech")
                        
                        # Seamlessly begin capturing the new command
                        self.audio_buffer.clear()
                        self.audio_buffer.append(chunk)
                        self.is_speaking_user = True
                        self.silence_frames = 0
                        self.speech_frames_count = 1
                else:
                    self.barge_in_counter = max(0, self.barge_in_counter - 1)

            # 3. State: LISTENING -> Capture User Speech
            elif current_state == SystemState.LISTENING:
                self.speaking_frame_count = 0
                self.barge_in_counter = 0
                self.audio_buffer.append(chunk)
                
                # Normal speech threshold (1000) for standard conversation
                has_speech = vad_engine.is_speech(chunk, threshold=1000.0)

                if has_speech:
                    self.speech_frames_count += 1
                    self.silence_frames = 0
                    self.is_speaking_user = True
                elif self.is_speaking_user:
                    self.silence_frames += 1

                # If user finished speaking (silence detected after speech)
                if self.is_speaking_user and self.silence_frames >= self.max_silence_frames:
                    if self.speech_frames_count >= self.min_speech_frames:
                        raw_audio = b"".join(self.audio_buffer)
                        self.audio_buffer.clear()
                        self.is_speaking_user = False
                        self.silence_frames = 0
                        self.speech_frames_count = 0

                        # Dispatch recorded audio for transcription & agent processing
                        asyncio.create_task(self._process_recorded_speech(raw_audio))
                    else:
                        # Spurious background click, reset buffer and go back to IDLE
                        self.audio_buffer.clear()
                        self.is_speaking_user = False
                        self.silence_frames = 0
                        self.speech_frames_count = 0
                        await state_manager.set_state(SystemState.IDLE)

        await audio_io.capture_continuous(_audio_chunk_handler)

    async def _process_recorded_speech(self, audio_bytes: bytes):
        """Transcribes speech, processes query through agent, and speaks response."""
        async with self._processing_lock:
            await state_manager.set_state(SystemState.THINKING)
            print("[VOICE] 🔄 Transcribing speech...")
            transcription = await asyncio.to_thread(stt_engine.transcribe_pcm, audio_bytes)
            
            if not transcription or not transcription.strip():
                print("[VOICE] No clear speech detected.")
                await state_manager.set_state(SystemState.IDLE)
                return

            print(f"\n[VOICE] 👤 User > {transcription}\n")
            response = await jarvis_agent.process_user_input(transcription)
            print(f"[VOICE] 🤖 JARVIS > {response}\n")
            
            # Speak response (can be interrupted at any moment)
            await tts_engine.speak(response)

    def stop(self):
        self.is_running = False
        tts_engine.stop()
        audio_io.stop_stream()

voice_listener = ContinuousVoiceListener()
