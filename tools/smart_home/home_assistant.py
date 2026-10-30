import os
import aiohttp
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class HomeAssistantTool(BaseTool):
    name = "home_assistant_control"
    description = "Turn on/off or toggle smart devices, lights, switches via Home Assistant."
    risk_level = "low"

    def get_parameters_schema(self):
        return {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "e.g., light, switch, climate"},
                "service": {"type": "string", "description": "e.g., turn_on, turn_off, toggle"},
                "entity_id": {"type": "string", "description": "e.g., light.living_room_lights"}
            },
            "required": ["domain", "service", "entity_id"]
        }

    async def execute(self, domain: str, service: str, entity_id: str, **kwargs):
        ha_url = os.getenv("HOME_ASSISTANT_URL", "http://localhost:8123")
        ha_token = os.getenv("HOME_ASSISTANT_TOKEN", "")
        
        url = f"{ha_url}/api/services/{domain}/{service}"
        headers = {"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"}
        payload = {"entity_id": entity_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        return f"Successfully executed {service} on {entity_id}."
                    return f"Failed with status {resp.status}"
        except Exception as e:
            return f"Home Assistant Connection Error: {str(e)}"