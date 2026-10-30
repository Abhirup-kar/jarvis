import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from core.event_bus import bus

class NodeInfo:
    def __init__(self, node_id: str, websocket, metadata: dict):
        self.node_id = node_id
        self.websocket = websocket
        self.os = metadata.get("os", "Unknown")
        self.hostname = metadata.get("hostname", node_id)
        self.ip = metadata.get("ip", "127.0.0.1")
        self.cpu_count = metadata.get("cpu_count", 1)
        self.connected_at = time.time()
        self.last_heartbeat = time.time()
        self.telemetry = {
            "cpu_percent": metadata.get("cpu_percent", 0.0),
            "ram_percent": metadata.get("ram_percent", 0.0),
            "disk_percent": metadata.get("disk_percent", 0.0)
        }
        self.status = "online"

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "os": self.os,
            "hostname": self.hostname,
            "ip": self.ip,
            "cpu_count": self.cpu_count,
            "uptime_seconds": int(time.time() - self.connected_at),
            "last_seen_seconds_ago": round(time.time() - self.last_heartbeat, 1),
            "telemetry": self.telemetry,
            "status": self.status
        }

class RemoteNodeManager:
    """Central Fleet Manager for coordinating connected remote machines."""

    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self._pending_tasks: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def register_node(self, websocket, metadata: dict) -> str:
        """Registers a newly connected remote node daemon."""
        node_id = metadata.get("node_id", f"node-{uuid.uuid4().hex[:6]}")
        
        async with self._lock:
            # If node already exists, close old connection
            if node_id in self.nodes:
                try:
                    await self.nodes[node_id].websocket.close()
                except Exception:
                    pass
            
            node = NodeInfo(node_id, websocket, metadata)
            self.nodes[node_id] = node

        print(f"\n[FLEET] 🚀 Node connected: '{node_id}' ({node.os} @ {node.hostname})")
        await bus.publish("node_connected", node.to_dict())
        await bus.publish("fleet_updated", self.list_nodes())
        return node_id

    async def unregister_node(self, node_id: str):
        """Removes a disconnected node."""
        async with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                print(f"[FLEET] ⚠️ Node disconnected: '{node_id}'")
        
        await bus.publish("node_disconnected", {"node_id": node_id})
        await bus.publish("fleet_updated", self.list_nodes())

    def update_telemetry(self, node_id: str, telemetry: dict):
        """Updates live CPU/RAM/Disk metrics for a node."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.last_heartbeat = time.time()
            node.telemetry.update(telemetry)

    def handle_task_response(self, task_id: str, result: Any, error: Optional[str] = None):
        """Resolves the awaiting future when a node sends back task execution results."""
        if task_id in self._pending_tasks:
            future = self._pending_tasks[task_id]
            if not future.done():
                if error:
                    future.set_exception(RuntimeError(error))
                else:
                    future.set_result(result)

    def list_nodes(self) -> List[dict]:
        """Returns inventory list of all online nodes."""
        return [node.to_dict() for node in self.nodes.values()]

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        return self.nodes.get(node_id)

    async def dispatch(self, node_id: str, action: str, payload: Any = None, timeout: float = 12.0) -> Any:
        """
        Sends an action directive to a target node (or 'all' nodes) and awaits result.
        """
        if not self.nodes:
            return {"error": "No remote machines are currently connected to JARVIS."}

        # Handle 'all' nodes broadcast
        if node_id.lower() in ("all", "fleet", "*"):
            results = {}
            for nid in list(self.nodes.keys()):
                results[nid] = await self.dispatch(nid, action, payload, timeout=timeout)
            return results

        node = self.nodes.get(node_id)
        if not node:
            available = list(self.nodes.keys())
            return {
                "error": f"Node '{node_id}' not found.",
                "available_nodes": available
            }

        task_id = f"task-{uuid.uuid4().hex[:8]}"
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_tasks[task_id] = future

        message = {
            "type": "command",
            "task_id": task_id,
            "action": action,
            "payload": payload
        }

        try:
            await node.websocket.send_text(json.dumps(message))
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {"error": f"Execution timed out on node '{node_id}' after {timeout}s"}
        except Exception as e:
            return {"error": f"Failed to dispatch to node '{node_id}': {str(e)}"}
        finally:
            self._pending_tasks.pop(task_id, None)

node_manager = RemoteNodeManager()

