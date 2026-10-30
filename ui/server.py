import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from core.event_bus import bus
from core.node_manager import node_manager
from config.settings import settings

app = FastAPI(title="JARVIS Holographic HUD & Fleet Hub")
STATIC_DIR = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

active_ui_connections = set()

@app.get("/")
async def get_hud():
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)

@app.get("/api/fleet")
async def get_fleet_inventory():
    """REST endpoint returning live status of all connected machines."""
    return JSONResponse(content={"nodes": node_manager.list_nodes()})

@app.websocket("/ws")
async def websocket_ui_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Web HUD clients."""
    await websocket.accept()
    active_ui_connections.add(websocket)
    
    # Send initial fleet state upon connecting
    await websocket.send_json({"event": "fleet_updated", "data": node_manager.list_nodes()})

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
                if isinstance(msg, dict) and msg.get("event") == "user_command":
                    # Lazy import to avoid circular dependencies
                    from core.agent import jarvis_agent
                    from voice.tts import tts_engine
                    
                    user_text = msg.get("text", "")
                    if user_text:
                        # Stop any speech playback immediately
                        tts_engine.stop()
                        print(f"\n[HUD USER] > {user_text}")
                        response_text = await jarvis_agent.process_user_input(user_text)
                        print(f"\n[HUD JARVIS] > {response_text}\n")
                        await broadcast_to_ui("agent_response", {"text": response_text})
                        asyncio.create_task(tts_engine.speak(response_text))
            except Exception as parse_err:
                print(f"[WS] Error processing command: {parse_err}")
    except WebSocketDisconnect:
        if websocket in active_ui_connections:
            active_ui_connections.remove(websocket)

@app.websocket("/ws/node")
async def websocket_node_endpoint(websocket: WebSocket):
    """WebSocket endpoint for remote machine edge daemons (agent_daemon.py)."""
    await websocket.accept()
    current_node_id = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
                msg_type = msg.get("type")

                # 1. Registration
                if msg_type == "register":
                    current_node_id = await node_manager.register_node(websocket, msg)
                    await broadcast_to_ui("fleet_updated", node_manager.list_nodes())

                # 2. Telemetry Heartbeat
                elif msg_type == "heartbeat":
                    node_id = msg.get("node_id", current_node_id)
                    telemetry = msg.get("telemetry", {})
                    node_manager.update_telemetry(node_id, telemetry)
                    await broadcast_to_ui("fleet_updated", node_manager.list_nodes())

                # 3. Remote Task Execution Result
                elif msg_type == "task_result":
                    task_id = msg.get("task_id")
                    result = msg.get("result")
                    error = msg.get("error")
                    node_manager.handle_task_response(task_id, result, error)

            except Exception as parse_err:
                print(f"[NODE WS ERROR] Error processing node message: {parse_err}")

    except WebSocketDisconnect:
        if current_node_id:
            await node_manager.unregister_node(current_node_id)
            await broadcast_to_ui("fleet_updated", node_manager.list_nodes())

async def broadcast_to_ui(event_type: str, data: dict):
    if not active_ui_connections:
        return
    payload = {"event": event_type, "data": data}
    for ws in list(active_ui_connections):
        try:
            await ws.send_json(payload)
        except Exception:
            if ws in active_ui_connections:
                active_ui_connections.remove(ws)

# Wire up EventBus to WebSocket Broadcasts
async def _on_hand_move(data):
    await broadcast_to_ui("hand_move", data)

async def _on_state_change(data):
    await broadcast_to_ui("state_change", data)

async def _on_sys_interrupt(data):
    await broadcast_to_ui("system_interrupted", data)

async def _on_wake_word(data):
    await broadcast_to_ui("wake_word_detected", data)

async def _on_fleet_update(data):
    await broadcast_to_ui("fleet_updated", data)

bus.subscribe("hand_coordinates", _on_hand_move)
bus.subscribe("state_changed", _on_state_change)
bus.subscribe("system_interrupted", _on_sys_interrupt)
bus.subscribe("wake_word_detected", _on_wake_word)
bus.subscribe("fleet_updated", _on_fleet_update)