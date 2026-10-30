from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    name: str
    description: str
    risk_level: str = "low"  # low, medium, high

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

    def to_openai_tool(self) -> Dict[str, Any]:
        schema = self.get_parameters_schema() or {}
        if not isinstance(schema, dict):
            schema = {"type": "object", "properties": {}, "required": []}
        if "type" not in schema:
            schema["type"] = "object"
        if "properties" not in schema:
            schema["properties"] = {}
        if "required" not in schema:
            schema["required"] = []

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema
            }
        }