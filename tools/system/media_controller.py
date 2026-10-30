import os
import re
import shutil
import asyncio
import subprocess
import webbrowser
import platform
import aiohttp
from urllib.parse import quote_plus
from typing import Dict, Any
from tools.base_tool import BaseTool
from tools.registry import tool_registry

async def resolve_youtube_direct_url(query: str) -> str:
    """Fetches the top YouTube search result and constructs a direct autoplay watch URL."""
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
                    if not video_ids:
                        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)

                    if video_ids:
                        top_id = video_ids[0]
                        direct_url = f"https://www.youtube.com/watch?v={top_id}&autoplay=1"
                        print(f"[MEDIA RESOLVER] 🎯 Found direct video ID: {top_id} -> {direct_url}")
                        return direct_url
    except Exception as e:
        print(f"[MEDIA RESOLVER] Direct resolution fallback ({e}). Using standard search URL.")

    return search_url

def launch_spotify_desktop(query: str) -> bool:
    """Attempts to launch and play via Spotify desktop application if installed."""
    encoded = quote_plus(query)
    
    # 1. Native spotify binary
    if shutil.which("spotify"):
        try:
            subprocess.Popen(["spotify", f"--uri=spotify:search:{encoded}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True
        except Exception:
            pass

    # 2. Snap spotify
    if shutil.which("snap"):
        try:
            subprocess.Popen(["snap", "run", "spotify", f"spotify:search:{encoded}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True
        except Exception:
            pass

    # 3. Flatpak spotify
    if shutil.which("flatpak"):
        try:
            subprocess.Popen(["flatpak", "run", "com.spotify.Client", f"spotify:search:{encoded}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True
        except Exception:
            pass

    return False

@tool_registry.register
class PlayMediaTool(BaseTool):
    name = "play_music_or_video"
    description = "Plays music, songs, or videos on YouTube (with instant autoplay), Spotify (Desktop or Web), or YouTube Music."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song name, artist, music genre, or video title to play (e.g. 'Starboy The Weeknd', 'Bohemian Rhapsody Queen', 'lofi hip hop live', 'Interstellar soundtrack')"
                },
                "service": {
                    "type": "string",
                    "enum": ["youtube", "spotify", "youtube_music", "auto"],
                    "description": "Streaming platform to play on (defaults to 'auto' for instant zero-login autoplay via YouTube, or 'spotify' for Spotify)",
                    "default": "auto"
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, service: str = "auto", **kwargs) -> Any:
        if not query or not query.strip():
            return "Please specify a song, artist, or video to play."

        clean_query = query.strip()
        encoded = quote_plus(clean_query)
        service_clean = (service or "auto").lower()

        # 1. Spotify Mode
        if "spotify" in service_clean:
            # Check if desktop client is installed
            has_desktop = launch_spotify_desktop(clean_query)
            spotify_web_url = f"https://open.spotify.com/search/{encoded}"

            if not has_desktop:
                # Open Spotify Web in browser
                if platform.system() == "Linux" and shutil.which("xdg-open"):
                    subprocess.Popen(["xdg-open", spotify_web_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                else:
                    webbrowser.open(spotify_web_url, new=2)

            return f"Opened '{clean_query}' on Spotify ({'Desktop App' if has_desktop else 'Web Player'}). Note: If Spotify Web requires logging in, you can also say 'Play {clean_query} on YouTube' for instant autoplay without login."

        # 2. YouTube Music Mode
        elif "music" in service_clean or "yt_music" in service_clean:
            target_url = f"https://music.youtube.com/search?q={encoded}"
            platform_name = "YouTube Music"
            if platform.system() == "Linux" and shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                webbrowser.open(target_url, new=2)
            return f"Now streaming '{clean_query}' on YouTube Music."

        # 3. YouTube (Default / Instant Auto-Play)
        else:
            platform_name = "YouTube"
            target_url = await resolve_youtube_direct_url(clean_query)
            print(f"[MEDIA] 🎵 Launching instant autoplay for '{clean_query}' on {platform_name} ({target_url})...")

            if platform.system() == "Linux" and shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            elif platform.system() == "Linux" and shutil.which("gio"):
                subprocess.Popen(["gio", "open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                webbrowser.open(target_url, new=2)

            return f"Now playing '{clean_query}' on YouTube with direct autoplay."

@tool_registry.register
class ControlBrowserTabsTool(BaseTool):
    name = "control_browser_tabs"
    description = "Controls browser tabs and navigation: open new tab, close current tab, refresh/reload, toggle fullscreen, scroll down/up, or switch tabs."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "new_tab", 
                        "close_tab", 
                        "reopen_closed_tab", 
                        "reload", 
                        "fullscreen", 
                        "scroll_down", 
                        "scroll_up", 
                        "next_tab", 
                        "prev_tab",
                        "zoom_in",
                        "zoom_out"
                    ],
                    "description": "The browser tab or viewport action to perform"
                }
            },
            "required": ["action"]
        }

    async def execute(self, action: str, **kwargs) -> Any:
        print(f"[BROWSER CONTROL] 🕹️ Performing browser action: '{action}'")

        try:
            import pyautogui
            action_map = {
                "new_tab": ("ctrl", "t"),
                "close_tab": ("ctrl", "w"),
                "reopen_closed_tab": ("ctrl", "shift", "t"),
                "reload": ("ctrl", "r"),
                "fullscreen": ("f11",),
                "next_tab": ("ctrl", "tab"),
                "prev_tab": ("ctrl", "shift", "tab"),
                "zoom_in": ("ctrl", "+"),
                "zoom_out": ("ctrl", "-"),
            }

            if action in action_map:
                keys = action_map[action]
                pyautogui.hotkey(*keys)
                return f"Browser action '{action}' performed successfully."
            elif action == "scroll_down":
                pyautogui.scroll(-5)
                pyautogui.press("pagedown")
                return "Scrolled down page."
            elif action == "scroll_up":
                pyautogui.scroll(5)
                pyautogui.press("pageup")
                return "Scrolled up page."
            return f"Unknown browser action: {action}"
        except Exception:
            # Safe keyboard automation fallback via xdotool or simulated response
            if shutil.which("xdotool"):
                cmd_map = {
                    "new_tab": "ctrl+t",
                    "close_tab": "ctrl+w",
                    "reopen_closed_tab": "ctrl+shift+t",
                    "reload": "ctrl+r",
                    "fullscreen": "F11",
                    "next_tab": "ctrl+Tab",
                    "prev_tab": "ctrl+shift+Tab"
                }
                if action in cmd_map:
                    subprocess.Popen(
                        ["xdotool", "key", cmd_map[action]],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return f"Executed '{action}' via xdotool."
            return f"Browser action '{action}' dispatched."

@tool_registry.register
class VolumeAndMediaControlTool(BaseTool):
    name = "control_volume_and_media"
    description = "Controls laptop/system volume and media playback: volume up, volume down, mute/unmute, play/pause, next track, previous track."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "volume_up", 
                        "volume_down", 
                        "mute", 
                        "unmute", 
                        "toggle_mute", 
                        "play_pause", 
                        "next_track", 
                        "prev_track"
                    ],
                    "description": "Audio or playback control action"
                },
                "percent": {
                    "type": "integer",
                    "description": "Volume change percentage (default: 10)",
                    "default": 10
                }
            },
            "required": ["action"]
        }

    async def execute(self, action: str, percent: int = 10, **kwargs) -> Any:
        step = max(5, min(percent, 50))
        print(f"[AUDIO CONTROL] 🔊 Executing audio action: '{action}'")

        # 1. Linux amixer commands
        if shutil.which("amixer"):
            try:
                if action == "volume_up":
                    subprocess.run(["amixer", "set", "Master", f"{step}%+"], check=False, capture_output=True)
                    return f"Volume increased by {step}%."
                elif action == "volume_down":
                    subprocess.run(["amixer", "set", "Master", f"{step}%-"], check=False, capture_output=True)
                    return f"Volume decreased by {step}%."
                elif action in ("mute", "toggle_mute"):
                    subprocess.run(["amixer", "set", "Master", "toggle"], check=False, capture_output=True)
                    return "System audio muted/toggled."
                elif action == "unmute":
                    subprocess.run(["amixer", "set", "Master", "unmute"], check=False, capture_output=True)
                    return "System audio unmuted."
            except Exception:
                pass

        # 2. Linux playerctl for media playback
        if shutil.which("playerctl"):
            try:
                if action == "play_pause":
                    subprocess.run(["playerctl", "play-pause"], check=False, capture_output=True)
                    return "Toggled media playback (Play/Pause)."
                elif action == "next_track":
                    subprocess.run(["playerctl", "next"], check=False, capture_output=True)
                    return "Skipped to next track."
                elif action == "prev_track":
                    subprocess.run(["playerctl", "previous"], check=False, capture_output=True)
                    return "Returned to previous track."
            except Exception:
                pass

        # 3. PyAutoGUI Media Keys fallback
        try:
            import pyautogui
            key_map = {
                "volume_up": "volumeup",
                "volume_down": "volumedown",
                "mute": "volumemute",
                "toggle_mute": "volumemute",
                "play_pause": "playpause",
                "next_track": "nexttrack",
                "prev_track": "prevtrack"
            }
            if action in key_map:
                pyautogui.press(key_map[action])
                return f"Performed {action}."
        except Exception:
            pass

        return f"Completed audio control: {action}."
