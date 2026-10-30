import os
import shutil
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class SystemStatusTool(BaseTool):
    name = "get_system_status"
    description = "Check current PC health: CPU utilization, Memory usage, disk storage, and system load."
    risk_level = "low"

    def get_parameters_schema(self):
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.2)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            return {
                "cpu_percent": f"{cpu}%",
                "memory_percent": f"{mem}%",
                "disk_percent": f"{disk}%",
                "status": "nominal"
            }
        except ImportError:
            # Fallback using standard library metrics
            disk_usage = shutil.disk_usage("/")
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
            return {
                "cpu_load_1m": load_avg[0],
                "disk_percent": f"{disk_percent:.1f}%",
                "status": "nominal (fallback metrics)"
            }