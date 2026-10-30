import unittest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from core.agent import JarvisAgent
from core.state import state_manager, SystemState

class TestAgent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent = JarvisAgent()
        # Mock the AsyncOpenAI client
        self.agent.client = MagicMock()
        self.agent.client.chat = MagicMock()
        self.agent.client.chat.completions = MagicMock()
        self.agent.client.chat.completions.create = AsyncMock()

    async def test_simple_chat_flow(self):
        mock_choice = MagicMock()
        mock_choice.message.tool_calls = None
        mock_choice.message.content = "All systems are operational, Sir."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        self.agent.client.chat.completions.create.return_value = mock_response

        response = await self.agent.process_user_input("What is your status?")
        self.assertEqual(response, "All systems are operational, Sir.")

    async def test_tool_call_flow(self):
        # First completion returns a tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_system_status"
        mock_tool_call.function.arguments = "{}"

        first_choice = MagicMock()
        first_choice.message.tool_calls = [mock_tool_call]
        first_choice.message.content = None
        first_resp = MagicMock()
        first_resp.choices = [first_choice]

        # Second completion returns final response
        second_choice = MagicMock()
        second_choice.message.tool_calls = None
        second_choice.message.content = "CPU load is 15% and memory is nominal."
        second_resp = MagicMock()
        second_resp.choices = [second_choice]

        self.agent.client.chat.completions.create.side_effect = [first_resp, second_resp]

        response = await self.agent.process_user_input("Check CPU utilization")
        self.assertEqual(response, "CPU load is 15% and memory is nominal.")
        self.assertEqual(self.agent.client.chat.completions.create.call_count, 2)

    async def test_tool_requires_confirmation_flow(self):
        # Step 1: Agent requests user confirmation
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_456"
        mock_tool_call.function.name = "send_email"
        mock_tool_call.function.arguments = '{"recipient": "boss@corp.com", "subject": "Alert", "body": "Classified data"}'

        mock_choice = MagicMock()
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.message.content = None
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        self.agent.client.chat.completions.create.return_value = mock_resp

        response1 = await self.agent.process_user_input("Send classified email to boss")
        self.assertIn("requires your confirmation", response1)
        self.assertIsNotNone(self.agent.pending_confirmation)

        # Step 2: User says "Yes, proceed" -> completes execution
        confirm_choice = MagicMock()
        confirm_choice.message.tool_calls = None
        confirm_choice.message.content = "Email dispatched successfully, Sir."
        confirm_resp = MagicMock()
        confirm_resp.choices = [confirm_choice]
        self.agent.client.chat.completions.create.return_value = confirm_resp

        response2 = await self.agent.process_user_input("Yes, proceed")
        self.assertIn("dispatched successfully", response2)
        self.assertIsNone(self.agent.pending_confirmation)

    async def test_tool_confirmation_denial_flow(self):
        # Agent requests confirmation
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_789"
        mock_tool_call.function.name = "send_email"
        mock_tool_call.function.arguments = '{"recipient": "test@corp.com", "subject": "Test", "body": "Data"}'

        mock_choice = MagicMock()
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.message.content = None
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        self.agent.client.chat.completions.create.return_value = mock_resp

        await self.agent.process_user_input("Send test email")
        self.assertIsNotNone(self.agent.pending_confirmation)

        # User says "No, cancel"
        cancel_response = await self.agent.process_user_input("No, cancel that")
        self.assertIn("cancelled", cancel_response.lower())
        self.assertIsNone(self.agent.pending_confirmation)

if __name__ == "__main__":
    unittest.main()
