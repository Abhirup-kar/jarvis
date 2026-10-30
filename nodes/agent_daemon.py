#!/usr/bin/env python3
"""
JARVIS Edge Node Daemon
Run this lightweight script on any remote computer (Mac / Windows / Linux)
to connect it to the central JARVIS platform.
"""

import os
import sys
import json
import time
import asyncio
import platform
import subprocess
import argparse
import socket
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

try:
    import websockets
except ImportError:
    websockets = None

class JarvisNodeDaemon:
    def __init__(self, hub_url: str, node_id: str = None, auth_token: str = "jarvis_secret_token"):
        self.hub_url = hub_url
        self.hostname = socket.gethostname()
        self.node_id = node_id or f"{platform.system().lower()}-{self.hostname.lower()}"
        self.auth_token = auth_token
        self.os_type = platform.system()
        self.is_running = True

    def get_telemetry(self) -> dict:
        """Collects current system metrics."""
        cpu = psutil.cpu_percent(interval=0.1) if psutil else 0.0
        ram = psutil.virtual_memory().percent if psutil else 0.0
        disk = psutil.disk_usage("/").percent if (psutil and hasattr(os, "statvfs")) else 0.0
        
        battery = None
        if psutil and hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat:
                battery = {"percent": bat.percent, "power_plugged": bat.power_plugged}

        return {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_percent": disk,
            "battery": battery
        }

    async def execute_action(self, action: str, payload: any) -> dict:
        """Executes a remote directive sent from the central JARVIS Core."""
        print(f"[NODE] ⚡ Executing action '{action}'...")
        
        # 1. System Health Status
        if action == "get_status":
            return {
                "node_id": self.node_id,
                "os": self.os_type,
                "hostname": self.hostname,
                "telemetry": self.get_telemetry(),
                "uptime": int(time.time() - (psutil.boot_time() if psutil else time.time()))
            }

        # 2. Run Shell / Terminal Command
        elif action == "run_command":
            cmd = payload if isinstance(payload, str) else payload.get("command", "")
            if not cmd:
                return {"error": "Empty command provided."}
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
                return {
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "returncode": proc.returncode
                }
            except asyncio.TimeoutError:
                return {"error": "Command timed out after 30 seconds."}
            except Exception as e:
                return {"error": str(e)}

        # 3. Launch Target Application
        elif action == "open_app":
            app_name = payload if isinstance(payload, str) else payload.get("app_name", "")
            try:
                if self.os_type == "Darwin":  # macOS
                    subprocess.Popen(["open", "-a", app_name])
                elif self.os_type == "Windows":
                    os.startfile(app_name)
                else:  # Linux
                    subprocess.Popen([app_name], start_new_session=True)
                return {"status": f"Successfully launched {app_name}"}
            except Exception as e:
                return {"error": f"Failed to launch {app_name}: {e}"}

        # 4. Native OS Toast Notification
        elif action == "notify":
            msg = payload if isinstance(payload, str) else payload.get("message", "")
            title = payload.get("title", "JARVIS Alert") if isinstance(payload, dict) else "JARVIS Alert"
            try:
                if self.os_type == "Darwin":
                    os.system(f"""osascript -e 'display notification "{msg}" with title "{title}"'""")
                elif self.os_type == "Linux":
                    subprocess.Popen(["notify-send", title, msg])
                return {"status": "Notification delivered"}
            except Exception as e:
                return {"error": str(e)}

        # 5. Remote Mouse / Keyboard Automation
        elif action == "click_or_type":
            try:
                import pyautogui
                act_type = payload.get("type", "type") if isinstance(payload, dict) else "type"
                if act_type == "click":
                    x, y = payload.get("x", 100), payload.get("y", 100)
                    pyautogui.click(x, y)
                elif act_type == "type":
                    text = payload.get("text", "")
                    pyautogui.typewrite(text)
                return {"status": "Desktop automation completed"}
            except Exception as e:
                return {"error": f"Desktop automation unavailable: {e}"}

        else:
            return {"error": f"Unknown action: '{action}'"}

    async def start(self):
        """Starts the persistent connection to Central JARVIS Hub."""
        if websockets is None:
            print("[ERROR] 'websockets' library is required. Install via: pip install websockets psutil")
            return

        print(f"============================================================")
        print(f" 🛰️  JARVIS Edge Node Daemon Online")
        print(f"============================================================")
        print(f" • Node ID:   {self.node_id}")
        print(f" • OS / Host: {self.os_type} ({self.hostname})")
        print(f" • Central:   {self.hub_url}")
        print(f"============================================================\n")

        while self.is_running:
            try:
                print(f"[NODE] Connecting to JARVIS Central Hub at {self.hub_url}...")
                async with websockets.connect(
                    self.hub_url,
                    extra_headers={"Authorization": f"Bearer {self.auth_token}"}
                ) as ws:
                    print("[NODE] ✅ Connected and authenticated with JARVIS Central Hub!")

                    # 1. Send Registration Payload
                    reg_data = {
                        "type": "register",
                        "node_id": self.node_id,
                        "os": self.os_type,
                        "hostname": self.hostname,
                        "cpu_count": os.cpu_count(),
                        **self.get_telemetry()
                    }
                    await ws.send(json.dumps(reg_data))

                    # 2. Start Periodic Telemetry Heartbeat Task
                    async def heartbeat_loop():
                        while True:
                            await asyncio.sleep(5.0)
                            hb = {
                                "type": "heartbeat",
                                "node_id": self.node_id,
                                "telemetry": self.get_telemetry()
                            }
                            await ws.send(json.dumps(hb))

                    hb_task = asyncio.create_task(heartbeat_loop())

                    # 3. Process Incoming Commands from Central JARVIS
                    try:
                        async for message in ws:
                            try:
                                data = json.loads(message)
                                if data.get("type") == "command":
                                    task_id = data.get("task_id")
                                    action = data.get("action")
                                    payload = data.get("payload")

                                    # Execute command
                                    result = await self.execute_action(action, payload)

                                    # Send back result
                                    response = {
                                        "type": "task_result",
                                        "task_id": task_id,
                                        "node_id": self.node_id,
                                        "result": result
                                    }
                                    await ws.send(json.dumps(response))
                            except Exception as e:
                                print(f"[NODE ERROR] Error processing command: {e}")
                    finally:
                        hb_task.cancel()

            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, OSError) as conn_err:
                print(f"[NODE] Connection lost ({conn_err}). Retrying in 5 seconds...")
                await asyncio.sleep(5.0)
            except Exception as e:
                print(f"[NODE] Unexpected error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5.0)

def main():
    parser = argparse.ArgumentParser(description="JARVIS Edge Node Daemon")
    parser.add_argument("--hub", default="ws://127.0.0.1:8000/ws/node", help="Central JARVIS WebSocket Hub URL")
    parser.add_argument("--node-id", default=None, help="Unique identifier for this machine")
    parser.add_argument("--token", default="jarvis_secret_token", help="Secret authentication token")
    args = parser.parse_args()

    daemon = JarvisNodeDaemon(hub_url=args.hub, node_id=args.node_id, auth_token=args.token)
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        print("\n[NODE] Shutting down node daemon.")

if __name__ == "__main__":
    main()

