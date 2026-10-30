import os
import json
import asyncio
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class MqttPublishTool(BaseTool):
    name = "mqtt_publish"
    description = "Publishes a message or command payload to an MQTT topic for smart devices (lights, switches, relays, Zigbee2MQTT, Tasmota)."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The MQTT topic to publish to (e.g. 'home/living_room/light/set' or 'zigbee2mqtt/lamp/set')"
                },
                "payload": {
                    "type": "string",
                    "description": "Message payload string or JSON string (e.g. '{\"state\": \"ON\", \"brightness\": 255}' or 'toggle')"
                },
                "qos": {
                    "type": "integer",
                    "description": "Quality of Service level (0, 1, or 2)",
                    "enum": [0, 1, 2],
                    "default": 0
                },
                "retain": {
                    "type": "boolean",
                    "description": "Whether to retain the message on broker",
                    "default": False
                }
            },
            "required": ["topic", "payload"]
        }

    async def execute(self, topic: str, payload: str, qos: int = 0, retain: bool = False, **kwargs) -> Dict[str, Any]:
        broker = os.getenv("MQTT_BROKER", "localhost")
        port = int(os.getenv("MQTT_PORT", 1883))

        # Try using paho-mqtt if available
        try:
            import paho.mqtt.publish as publish
            
            def _sync_publish():
                publish.single(
                    topic=topic,
                    payload=payload,
                    qos=qos,
                    retain=retain,
                    hostname=broker,
                    port=port,
                    timeout=5
                )

            await asyncio.to_thread(_sync_publish)
            return {
                "status": "success",
                "message": f"Successfully published payload to MQTT topic '{topic}'",
                "broker": f"{broker}:{port}",
                "topic": topic,
                "payload": payload,
                "qos": qos,
                "retain": retain
            }
        except ImportError:
            # Graceful fallback simulation when paho-mqtt is not installed
            return {
                "status": "simulated",
                "message": f"[Simulated Mode] MQTT message queued for topic '{topic}' (paho-mqtt not installed).",
                "broker": f"{broker}:{port}",
                "topic": topic,
                "payload": payload
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to publish MQTT message to {broker}:{port}: {str(e)}",
                "topic": topic,
                "payload": payload
            }

