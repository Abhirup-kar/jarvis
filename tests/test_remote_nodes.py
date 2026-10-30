import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from core.node_manager import RemoteNodeManager, NodeInfo
from tools.system.remote_nodes import ListConnectedNodesTool, RemoteMachineControlTool
from tools.registry import tool_registry

class TestRemoteNodes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.node_manager = RemoteNodeManager()

    async def test_node_registration_and_list(self):
        mock_ws = AsyncMock()
        metadata = {
            "node_id": "test-macbook",
            "os": "Darwin",
            "hostname": "Abhirup-Mac",
            "cpu_percent": 12.5,
            "ram_percent": 45.0
        }
        
        node_id = await self.node_manager.register_node(mock_ws, metadata)
        self.assertEqual(node_id, "test-macbook")
        
        nodes = self.node_manager.list_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["node_id"], "test-macbook")
        self.assertEqual(nodes[0]["os"], "Darwin")
        self.assertEqual(nodes[0]["telemetry"]["cpu_percent"], 12.5)

    async def test_node_telemetry_update(self):
        mock_ws = AsyncMock()
        await self.node_manager.register_node(mock_ws, {"node_id": "server-linux", "os": "Linux"})
        
        self.node_manager.update_telemetry("server-linux", {"cpu_percent": 88.0, "ram_percent": 60.0})
        node = self.node_manager.get_node("server-linux")
        self.assertIsNotNone(node)
        self.assertEqual(node.telemetry["cpu_percent"], 88.0)

    async def test_node_dispatch_and_response(self):
        mock_ws = AsyncMock()
        await self.node_manager.register_node(mock_ws, {"node_id": "win-desktop", "os": "Windows"})

        # Coroutine to simulate remote node answering back with task result
        async def simulate_node_reply():
            await asyncio.sleep(0.05)
            # Find the active task id from mock_ws.send_text
            self.assertTrue(mock_ws.send_text.called)
            sent_payload = mock_ws.send_text.call_args[0][0]
            import json
            data = json.loads(sent_payload)
            task_id = data["task_id"]
            self.node_manager.handle_task_response(task_id, {"stdout": "hello from windows", "returncode": 0})

        asyncio.create_task(simulate_node_reply())

        result = await self.node_manager.dispatch("win-desktop", "run_command", "echo hello", timeout=2.0)
        self.assertEqual(result.get("stdout"), "hello from windows")

    async def test_node_unregistration(self):
        mock_ws = AsyncMock()
        await self.node_manager.register_node(mock_ws, {"node_id": "temp-node", "os": "Linux"})
        self.assertEqual(len(self.node_manager.list_nodes()), 1)

        await self.node_manager.unregister_node("temp-node")
        self.assertEqual(len(self.node_manager.list_nodes()), 0)

    async def test_list_connected_nodes_tool(self):
        tool = ListConnectedNodesTool()
        schema = tool.to_openai_tool()
        self.assertEqual(schema["function"]["name"], "list_connected_nodes")

        # Execute when empty
        result = await tool.execute()
        self.assertIn("connected_count", result)

    async def test_remote_machine_control_tool_schema(self):
        tool = RemoteMachineControlTool()
        schema = tool.to_openai_tool()
        self.assertEqual(schema["function"]["name"], "remote_machine_control")
        self.assertIn("node_id", schema["function"]["parameters"]["properties"])
        self.assertIn("action", schema["function"]["parameters"]["properties"])

if __name__ == "__main__":
    unittest.main()

