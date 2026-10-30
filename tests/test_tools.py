import unittest
import asyncio
import tempfile
from pathlib import Path
from tools.registry import ToolRegistry, tool_registry
from tools.system.os_control import SystemStatusTool
from tools.system.desktop_bot import DesktopClickTypeTool
from tools.system.app_launcher import OpenBrowserTool, LaunchApplicationTool, ExecuteTerminalCommandTool
from tools.system.media_controller import PlayMediaTool, ControlBrowserTabsTool, VolumeAndMediaControlTool
from tools.system.desktop_operator import (
    TakeDesktopScreenshotTool,
    ManageDesktopWindowsTool,
    ManageSystemFilesTool,
    ManageSystemProcessesTool,
    ClipboardControlTool
)
from tools.smart_home.mqtt_client import MqttPublishTool
from tools.staff_automations.document_ops import ReadDocumentTool, WriteDocumentTool, ListDocumentsTool
from tools.staff_automations.comms import SendEmailTool, SendNotificationTool

class TestTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_tool_registration_and_schema(self):
        self.registry.register(SystemStatusTool)
        tool = self.registry.get_tool("get_system_status")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "get_system_status")

        openai_tools = self.registry.get_openai_tools()
        self.assertEqual(len(openai_tools), 1)
        self.assertEqual(openai_tools[0]["type"], "function")
        self.assertEqual(openai_tools[0]["function"]["name"], "get_system_status")

    def test_auto_discovery(self):
        tool_registry.auto_discover()
        discovered_names = [t["function"]["name"] for t in tool_registry.get_openai_tools()]
        self.assertIn("get_system_status", discovered_names)
        self.assertIn("mqtt_publish", discovered_names)
        self.assertIn("send_email", discovered_names)
        self.assertIn("read_document", discovered_names)
        self.assertIn("open_browser", discovered_names)
        self.assertIn("launch_application", discovered_names)
        self.assertIn("execute_terminal_command", discovered_names)
        self.assertIn("play_music_or_video", discovered_names)
        self.assertIn("control_browser_tabs", discovered_names)
        self.assertIn("control_volume_and_media", discovered_names)
        self.assertIn("take_desktop_screenshot", discovered_names)
        self.assertIn("manage_desktop_windows", discovered_names)
        self.assertIn("manage_system_files", discovered_names)
        self.assertIn("manage_system_processes", discovered_names)
        self.assertIn("clipboard_control", discovered_names)

    async def test_system_status_execution(self):
        tool = SystemStatusTool()
        result = await tool.execute()
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

    async def test_desktop_operator_tools(self):
        # 1. Screenshot
        screenshot_tool = TakeDesktopScreenshotTool()
        res_screen = await screenshot_tool.execute()
        self.assertIn("status", res_screen)

        # 2. Window Manager
        win_tool = ManageDesktopWindowsTool()
        res_win = await win_tool.execute(action="list")
        self.assertIn("open_windows", res_win)

        # 3. Process Manager
        proc_tool = ManageSystemProcessesTool()
        res_proc = await proc_tool.execute(action="list")
        self.assertIn("top_processes", res_proc)

        # 4. Clipboard
        clip_tool = ClipboardControlTool()
        res_copy = await clip_tool.execute(action="copy", text="JARVIS Autonomous Protocol")
        self.assertIsInstance(res_copy, str)

    async def test_manage_system_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_tool = ManageSystemFilesTool()
            test_file = str(Path(temp_dir) / "test_script.py")

            # Write file
            res_write = await file_tool.execute(action="write", path=test_file, content="print('hello jarvis')")
            self.assertIn("Successfully written", res_write)

            # Read file
            res_read = await file_tool.execute(action="read", path=test_file)
            self.assertEqual(res_read.get("content"), "print('hello jarvis')")

            # Copy file
            copy_file = str(Path(temp_dir) / "test_script_copy.py")
            res_copy = await file_tool.execute(action="copy", path=test_file, destination=copy_file)
            self.assertIn("Copied", res_copy)

            # List dir
            res_list = await file_tool.execute(action="list_dir", path=temp_dir)
            self.assertEqual(res_list.get("total_count"), 2)

            # Delete file
            res_del = await file_tool.execute(action="delete", path=copy_file)
            self.assertIn("Successfully deleted", res_del)

    async def test_media_and_browser_tools(self):
        play_tool = PlayMediaTool()
        self.assertEqual(play_tool.name, "play_music_or_video")
        self.assertIn("query", play_tool.get_parameters_schema()["properties"])

        # Test YouTube execution formatting
        yt_res = await play_tool.execute(query="Bohemian Rhapsody", service="youtube")
        self.assertIn("Bohemian Rhapsody", yt_res)

        # Test Spotify execution formatting
        spot_res = await play_tool.execute(query="Starboy", service="spotify")
        self.assertIn("Starboy", spot_res)

        browser_ctrl = ControlBrowserTabsTool()
        self.assertEqual(browser_ctrl.name, "control_browser_tabs")
        tab_res = await browser_ctrl.execute(action="new_tab")
        self.assertIsInstance(tab_res, str)

        vol_ctrl = VolumeAndMediaControlTool()
        self.assertEqual(vol_ctrl.name, "control_volume_and_media")
        vol_res = await vol_ctrl.execute(action="volume_up", percent=10)
        self.assertIsInstance(vol_res, str)

    async def test_app_launcher_schemas(self):
        browser_tool = OpenBrowserTool()
        self.assertEqual(browser_tool.name, "open_browser")
        self.assertIn("url", browser_tool.get_parameters_schema()["properties"])

        app_tool = LaunchApplicationTool()
        self.assertEqual(app_tool.name, "launch_application")
        self.assertIn("app_name", app_tool.get_parameters_schema()["properties"])

        exec_tool = ExecuteTerminalCommandTool()
        self.assertEqual(exec_tool.name, "execute_terminal_command")
        self.assertIn("command", exec_tool.get_parameters_schema()["properties"])

    async def test_execute_terminal_command(self):
        exec_tool = ExecuteTerminalCommandTool()
        result = await exec_tool.execute(command="echo 'jarvis online'")
        self.assertIn("jarvis online", result)

    async def test_mqtt_publish_execution(self):
        tool = MqttPublishTool()
        result = await tool.execute(topic="test/topic", payload="ON")
        self.assertIn("status", result)
        self.assertEqual(result["topic"], "test/topic")

    async def test_document_ops_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_tool = WriteDocumentTool()
            read_tool = ReadDocumentTool()
            test_file = str(Path(temp_dir) / "test_note.txt")

            # Write document
            write_res = await write_tool.execute(file_name=test_file, content="JARVIS Protocol Active")
            self.assertEqual(write_res.get("status"), "success")

            # Read document
            read_res = await read_tool.execute(file_path=test_file)
            self.assertEqual(read_res.get("status"), "success")
            self.assertEqual(read_res.get("content"), "JARVIS Protocol Active")

    async def test_comms_simulation(self):
        tool = SendEmailTool()
        result = await tool.execute(recipient="stark@example.com", subject="Armor Diagnostic", body="All systems green.")
        self.assertIn("status", result)

        notify_tool = SendNotificationTool()
        notify_res = await notify_tool.execute(message="Security alert triggered")
        self.assertIn("status", notify_res)

if __name__ == "__main__":
    unittest.main()
