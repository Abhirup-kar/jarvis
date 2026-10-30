import os
import shutil
import asyncio
import subprocess
import webbrowser
import platform
from typing import Dict, Any
from tools.base_tool import BaseTool
from tools.registry import tool_registry

COMMON_APP_MAP = {
    "browser": ["xdg-open", "https://google.com"],
    "chrome": ["google-chrome", "google-chrome-stable", "chromium", "xdg-open", "https://google.com"],
    "firefox": ["firefox", "xdg-open", "https://google.com"],
    "brave": ["brave-browser", "brave", "xdg-open", "https://google.com"],
    "code": ["code", "/usr/bin/code"],
    "vscode": ["code", "/usr/bin/code"],
    "vs code": ["code", "/usr/bin/code"],
    "terminal": ["gnome-terminal", "x-terminal-emulator", "tilix", "alacritty", "konsole", "xfce4-terminal"],
    "calculator": ["gnome-calculator", "kcalc", "calculator"],
    "files": ["nautilus", "nemo", "dolphin", "thunar", "xdg-open", "."],
    "file manager": ["nautilus", "nemo", "dolphin", "thunar", "xdg-open", "."],
    "settings": ["gnome-control-center", "systemsettings", "xfce4-settings-manager"],
    "text editor": ["gedit", "kate", "mousepad", "gnome-text-editor"],
    "spotify": ["spotify", "flatpak run com.spotify.Client"],
    "vlc": ["vlc", "flatpak run org.videolan.VLC"]
}

@tool_registry.register
class OpenBrowserTool(BaseTool):
    name = "open_browser"
    description = "Opens the web browser and navigates directly to a target website or URL (e.g. YouTube, Google, GitHub, ChatGPT, Reddit, Wikipedia, or any search query) on the physical screen."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL, website name, or query to open (e.g. 'https://youtube.com', 'github.com', 'google.com', or 'openai')"
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str = "https://google.com", **kwargs) -> Any:
        target = (url or "").strip()
        if not target:
            target = "https://google.com"

        # Format URL properly
        if not target.startswith("http://") and not target.startswith("https://"):
            if "." in target and not " " in target:
                target = f"https://{target}"
            else:
                # Treat as search query
                from urllib.parse import quote_plus
                target = f"https://www.google.com/search?q={quote_plus(target)}"

        print(f"[APP LAUNCHER] 🌐 Opening browser URL: {target}")

        try:
            # 1. Try system xdg-open / gio on Linux first (silencing stderr to prevent browser noise)
            if platform.system() == "Linux":
                if shutil.which("xdg-open"):
                    subprocess.Popen(
                        ["xdg-open", target], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        start_new_session=True
                    )
                    return f"Successfully opened {target} in default web browser."
                elif shutil.which("gio"):
                    subprocess.Popen(
                        ["gio", "open", target], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        start_new_session=True
                    )
                    return f"Successfully opened {target} in default web browser."

            # 2. Universal Python webbrowser fallback
            opened = webbrowser.open(target, new=2)
            if opened:
                return f"Successfully opened {target} in web browser."
            return f"Requested opening {target}."
        except Exception as e:
            return f"Error launching browser: {str(e)}"

@tool_registry.register
class LaunchApplicationTool(BaseTool):
    name = "launch_application"
    description = "Launches any desktop application or software on the user's laptop (e.g. VS Code, Terminal, Files / File Manager, Calculator, Browser, Spotify, Settings, Text Editor)."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name or identifier of the app to open (e.g. 'code', 'terminal', 'calculator', 'files', 'browser', 'spotify', 'settings')"
                }
            },
            "required": ["app_name"]
        }

    async def execute(self, app_name: str, **kwargs) -> Any:
        if not app_name or not app_name.strip():
            return "Please provide the name of the application to open."

        app_clean = app_name.strip().lower()
        print(f"[APP LAUNCHER] 🚀 Launching application: '{app_clean}'")

        # Check in common application map
        candidates = COMMON_APP_MAP.get(app_clean, [app_clean])

        # Try launching candidates
        for cand in candidates:
            if isinstance(cand, list):
                cmd = cand
                bin_name = cmd[0]
            else:
                cmd = [cand]
                bin_name = cand

            if shutil.which(bin_name):
                try:
                    subprocess.Popen(
                        cmd, 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        start_new_session=True
                    )
                    return f"Successfully launched {app_name}."
                except Exception:
                    continue

        # Try gtk-launch (GNOME / Linux Desktop entries)
        if shutil.which("gtk-launch"):
            try:
                subprocess.Popen(
                    ["gtk-launch", f"{app_clean}.desktop"], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL, 
                    start_new_session=True
                )
                return f"Successfully launched {app_name} via desktop launcher."
            except Exception:
                pass

        # Try Flatpak / Snap
        if shutil.which("flatpak"):
            try:
                subprocess.Popen(
                    ["flatpak", "run", app_clean], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL, 
                    start_new_session=True
                )
                return f"Launched {app_name} via Flatpak."
            except Exception:
                pass

        # Universal fallback: xdg-open
        if shutil.which("xdg-open"):
            try:
                subprocess.Popen(
                    ["xdg-open", app_clean], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL, 
                    start_new_session=True
                )
                return f"Requested opening {app_name}."
            except Exception:
                pass

        return f"Could not find or open application '{app_name}'. Please verify it is installed."

@tool_registry.register
class ExecuteTerminalCommandTool(BaseTool):
    name = "execute_terminal_command"
    description = "Executes a shell or terminal command on the local machine and returns the stdout output."
    risk_level = "medium"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute (e.g. 'ls -la', 'ps aux', 'git status')"
                }
            },
            "required": ["command"]
        }

    async def execute(self, command: str, **kwargs) -> Any:
        if not command or not command.strip():
            return "No command provided."

        print(f"[SHELL EXEC] 💻 Running command: {command}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20.0)
            out_str = stdout.decode("utf-8", errors="replace")
            err_str = stderr.decode("utf-8", errors="replace")
            
            if proc.returncode == 0:
                return out_str if out_str else f"Command completed successfully with exit code 0."
            return f"Command returned exit code {proc.returncode}:\n{err_str if err_str else out_str}"
        except asyncio.TimeoutError:
            return "Command execution timed out after 20 seconds."
        except Exception as e:
            return f"Execution error: {str(e)}"
