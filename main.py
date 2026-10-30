import os
import sys
import asyncio
import logging
import uvicorn
from config.settings import settings
from tools.registry import tool_registry
from vision.tracker import hand_tracker
from core.agent import jarvis_agent
from voice.tts import tts_engine
from voice.listener import voice_listener
from ui.server import app

# Silence verbose uvicorn access logs to keep terminal clean
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

async def run_interactive_terminal():
    """High-performance, non-blocking asynchronous CLI loop for typing directives to JARVIS."""
    await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(" 🤖  J.A.R.V.I.S. ONLINE & READY")
    print("=" * 60)
    print(f" • LLM Model:  {settings.LLM_MODEL}")
    print(f" • Web HUD:    http://{settings.HOST}:{settings.PORT}")
    print(f" • Voice:      Active on microphone (Barge-in enabled)")
    print(f" • Terminal:   Type any command & press Enter (or 'exit' to quit)")
    print("=" * 60 + "\n")
    
    loop = asyncio.get_running_loop()
    
    # Connect native Linux asynchronous pipe reader on stdin
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    try:
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    except Exception:
        reader = None

    while True:
        try:
            # Print prompt prompt prefix
            sys.stdout.write("JARVIS ❯ ")
            sys.stdout.flush()

            if reader is not None:
                line_bytes = await reader.readline()
                if not line_bytes:
                    await asyncio.sleep(0.2)
                    continue
                user_input = line_bytes.decode("utf-8", errors="ignore")
            else:
                user_input = await loop.run_in_executor(None, sys.stdin.readline)

            text = user_input.strip() if user_input else ""
            if not text:
                continue

            if text.lower() in ["exit", "quit", "q"]:
                print("\n[JARVIS] Powering down systems. Goodbye, Sir.\n")
                voice_listener.stop()
                sys.exit(0)

            # Instantly stop any previous speech playback
            tts_engine.stop()

            print(f"\n[USER] > {text}")
            response = await jarvis_agent.process_user_input(text)
            print(f"\n[JARVIS] > {response}\n")

            # Speak response asynchronously (interruptible)
            asyncio.create_task(tts_engine.speak(response))

        except (KeyboardInterrupt, EOFError):
            print("\n[JARVIS] Terminating terminal session.")
            break
        except Exception as e:
            print(f"[TERMINAL ERROR] {e}")
            await asyncio.sleep(0.5)

async def main():
    # 1. Discover all tools
    tool_registry.auto_discover()
    
    # 2. Configure Web Server
    server_config = uvicorn.Config(
        app, 
        host=settings.HOST, 
        port=settings.PORT, 
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(server_config)

    # 3. Start all subsystems concurrently
    await asyncio.gather(
        server.serve(),
        hand_tracker.start_stream(),
        voice_listener.start(),
        run_interactive_terminal()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[JARVIS] System shut down.")