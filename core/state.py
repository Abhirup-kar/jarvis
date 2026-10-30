from enum import Enum
import asyncio
from core.event_bus import bus

class SystemState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"

class StateManager:
    def __init__(self):
        self._current_state: SystemState = SystemState.IDLE
        self._lock = asyncio.Lock()

    @property
    def current(self) -> SystemState:
        return self._current_state

    async def set_state(self, new_state: SystemState):
        async with self._lock:
            if self._current_state != new_state:
                old_state = self._current_state
                self._current_state = new_state
                await bus.publish("state_changed", {"from": old_state.value, "to": new_state.value})

state_manager = StateManager()