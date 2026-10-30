import asyncio
from core.state import state_manager, SystemState
from core.event_bus import bus

class InterruptController:
    def __init__(self):
        self.interrupt_event = asyncio.Event()

    async def trigger_barge_in(self, reason: str = "user_speech"):
        """Instant Gemini-style interruption: cuts off TTS audio and starts listening."""
        # 1. Lazy import to avoid circular dependencies
        from voice.tts import tts_engine
        
        current_state = state_manager.current
        if current_state in (SystemState.SPEAKING, SystemState.THINKING, SystemState.EXECUTING):
            print(f"\n[BARGE-IN] ⚡ Interruption triggered ({reason}). Cutting off speech...")
            self.interrupt_event.set()
            
            # Immediately kill TTS sound output
            tts_engine.stop()
            
            # Switch state to LISTENING immediately
            await state_manager.set_state(SystemState.LISTENING)
            await bus.publish("system_interrupted", {"reason": reason})
            
            # Reset event for next interaction
            self.interrupt_event.clear()

    def is_interrupted(self) -> bool:
        return self.interrupt_event.is_set()

interrupt_controller = InterruptController()