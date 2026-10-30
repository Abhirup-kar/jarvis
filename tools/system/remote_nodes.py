from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from core.node_manager import node_manager

class ListConnectedNodesTool(BaseTool):
    name = "list_connected_nodes"
    description = "Lists all online connected remote machines (PCs, Macs, Linux servers, Raspberry Pis) in the JARVIS fleet with live OS and CPU/RAM health."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        nodes = node_manager.list_nodes()
        if not nodes:
            return {
                "message": "No remote machines are currently connected. Run 'python nodes/agent_daemon.py' on target machines to connect them to JARVIS.",
                "connected_count": 0,
                "nodes": []
            }
        return {
            "connected_count": len(nodes),
            "nodes": nodes
        }

class RemoteMachineControlTool(BaseTool):
    name = "remote_machine_control"
    description = "Executes shell commands, checks hardware status, opens apps, or displays alerts on connected remote computers or servers."
    risk_level = "medium"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The target machine ID (e.g. 'office-macbook', 'linux-server', or 'all' for all connected machines)"
                },
                "action": {
                    "type": "string",
                    "enum": ["get_status", "run_command", "open_app", "notify", "click_or_type"],
                    "description": "Action to execute on target machine"
                },
                "payload": {
                    "type": "string",
                    "description": "Command to run, app name to open, or notification message"
                }
            },
            "required": ["node_id", "action", "payload"]
        }

    async def execute(self, node_id: str, action: str, payload: Any = "", **kwargs) -> Any:
        if not node_id:
            return {"error": "Target node_id is required."}
        
        result = await node_manager.dispatch(node_id, action, payload)
        return {
            "target_node": node_id,
            "action": action,
            "result": result
        }

