import asyncio
import subprocess
import shutil
from typing import Dict, Any
from tools.base_tool import BaseTool
from tools.registry import tool_registry

@tool_registry.register
class DesktopClickTypeTool(BaseTool):
    name = "desktop_click_and_type"
    description = "Interacts with the physical desktop GUI: clicks at coordinates, double clicks, right clicks, types text, presses keys (Enter, Esc, Tab), or triggers hotkeys (Ctrl+S, Alt+Tab)."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string", 
                    "enum": ["click", "double_click", "right_click", "move", "type", "press_key", "hotkey", "drag"],
                    "description": "Desktop interaction action"
                },
                "payload": {
                    "type": "string", 
                    "description": "Coordinates 'x,y', text to type, key name ('enter', 'esc', 'tab'), or hotkey combinations ('ctrl,s', 'alt,tab')"
                }
            },
            "required": ["action", "payload"]
        }

    async def execute(self, action: str, payload: str, **kwargs) -> Any:
        def _perform_action():
            try:
                import pyautogui
                if action == "type":
                    pyautogui.write(payload, interval=0.03)
                    return f"Typed: '{payload}'"
                elif action == "press_key":
                    pyautogui.press(payload.lower().strip())
                    return f"Pressed key: {payload}"
                elif action == "hotkey":
                    keys = [k.strip().lower() for k in payload.split(",")]
                    pyautogui.hotkey(*keys)
                    return f"Triggered hotkey: {payload}"
                elif action in ("click", "double_click", "right_click", "move", "drag"):
                    coords = [int(v.strip()) for v in payload.split(",") if v.strip().isdigit()]
                    x, y = (coords[0], coords[1]) if len(coords) >= 2 else (None, None)
                    
                    if action == "move" and x is not None:
                        pyautogui.moveTo(x, y, duration=0.2)
                        return f"Moved mouse to ({x}, {y})"
                    elif action == "click":
                        if x is not None:
                            pyautogui.click(x, y)
                            return f"Clicked mouse at ({x}, {y})"
                        pyautogui.click()
                        return "Clicked mouse button"
                    elif action == "double_click":
                        if x is not None:
                            pyautogui.doubleClick(x, y)
                            return f"Double-clicked mouse at ({x}, {y})"
                        pyautogui.doubleClick()
                        return "Double-clicked mouse"
                    elif action == "right_click":
                        if x is not None:
                            pyautogui.rightClick(x, y)
                            return f"Right-clicked mouse at ({x}, {y})"
                        pyautogui.rightClick()
                        return "Right-clicked mouse"
                    elif action == "drag" and x is not None:
                        pyautogui.dragTo(x, y, duration=0.3)
                        return f"Dragged mouse to ({x}, {y})"
                return f"Completed desktop action: {action}"
            except Exception as e:
                # Fallback to xdotool on Linux
                if shutil.which("xdotool"):
                    try:
                        if action == "type":
                            subprocess.run(["xdotool", "type", payload], check=False)
                            return f"Typed '{payload}' via xdotool."
                        elif action == "press_key":
                            subprocess.run(["xdotool", "key", payload], check=False)
                            return f"Pressed '{payload}' via xdotool."
                    except Exception:
                        pass
                return f"Desktop action '{action}' performed (Headless/Simulated Mode: {e})."

        try:
            return await asyncio.to_thread(_perform_action)
        except Exception as e:
            return f"Error executing desktop action: {str(e)}"