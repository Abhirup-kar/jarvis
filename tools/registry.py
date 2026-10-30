import importlib
import inspect
import pkgutil
from typing import Dict
from tools.base_tool import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool_cls):
        tool_instance = tool_cls()
        self._tools[tool_instance.name] = tool_instance
        return tool_cls

    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def get_openai_tools(self):
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def auto_discover(self):
        import tools
        for _, module_name, is_pkg in pkgutil.walk_packages(tools.__path__, tools.__name__ + "."):
            if not is_pkg:
                module = importlib.import_module(module_name)
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, BaseTool) and cls is not BaseTool:
                        self.register(cls)

tool_registry = ToolRegistry()