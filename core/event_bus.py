import asyncio
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any = None):
        if event_type in self._subscribers:
            tasks = []
            for handler in self._subscribers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler(data)))
                else:
                    try:
                        res = handler(data)
                        if asyncio.iscoroutine(res):
                            tasks.append(asyncio.create_task(res))
                    except Exception as e:
                        print(f"[EVENT BUS ERROR] Handler for {event_type} failed: {e}")
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

bus = EventBus()