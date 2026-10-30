import asyncio
import io
import os
import shutil
from config.settings import settings
from core.state import state_manager, SystemState

class TextToSpeech:
    def __init__(self):
        self.voice = settings.TTS_VOICE
        self.current_process = None
        self.is_speaking = False
        self._speak_lock = asyncio.Lock()

    def stop(self):
        """Immediately stops/kills any ongoing speech playback in real-time."""
        self.is_speaking = False
        if self.current_process is not None:
            try:
                self.current_process.kill()
            except Exception:
                pass
            self.current_process = None
            print("[TTS] Audio playback stopped immediately (Barge-in).")

    async def speak(self, text: str):
        if not text or not text.strip():
            return

        async with self._speak_lock:
            # Stop any previous playback first
            self.stop()
            self.is_speaking = True
            await state_manager.set_state(SystemState.SPEAKING)

            try:
                import edge_tts
                print(f"[TTS] 🔊 Generating audio with voice '{self.voice}'...")
                communicate = edge_tts.Communicate(text, self.voice)
                audio_stream = io.BytesIO()

                # Stream audio chunks with quick interruption check
                async for chunk in communicate.stream():
                    if not self.is_speaking:
                        return
                    if chunk["type"] == "audio":
                        audio_stream.write(chunk["data"])

                if not self.is_speaking or audio_stream.tell() == 0:
                    return

                audio_stream.seek(0)
                temp_file = settings.STORAGE_DIR / "temp_tts.mp3"
                with open(temp_file, "wb") as f:
                    f.write(audio_stream.read())

                # Find available media player: ffplay, mpv, afplay, or aplay
                player = None
                for candidate in ["ffplay", "mpv", "afplay", "aplay"]:
                    if shutil.which(candidate):
                        player = candidate
                        break

                if player and self.is_speaking:
                    if player == "ffplay":
                        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(temp_file)]
                    else:
                        cmd = [player, str(temp_file)]

                    print(f"[TTS] ▶️  Playing audio via {player}...")
                    self.current_process = await asyncio.create_subprocess_exec(*cmd)

                    # Monitor process completion while allowing instant kill
                    while self.is_speaking and self.current_process and self.current_process.returncode is None:
                        try:
                            await asyncio.wait_for(self.current_process.wait(), timeout=0.05)
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            break
                elif self.is_speaking:
                    # Simulated audio duration fallback
                    duration = min(max(len(text) * 0.05, 0.5), 5.0)
                    for _ in range(int(duration * 20)):
                        if not self.is_speaking:
                            break
                        await asyncio.sleep(0.05)

            except Exception as e:
                print(f"[TTS ERROR] Speech synthesis failed: {e}")
            finally:
                self.current_process = None
                # Only reset state to IDLE if we weren't interrupted into LISTENING
                if state_manager.current == SystemState.SPEAKING:
                    await state_manager.set_state(SystemState.IDLE)
                self.is_speaking = False

tts_engine = TextToSpeech()