import asyncio
import json
import os
import time
from typing import Dict, Any, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import threading
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from contextlib import asynccontextmanager


PIXERA_HOST = os.getenv("PIXERA_HOST", "192.168.68.76")
PIXERA_PORT = int(os.getenv("PIXERA_PORT", "4023"))

# ------------------------------
# PIXERA METHOD MAP
# ------------------------------
PIXERA_METHODS = {
    "GET_TIMELINES": "Pixera.Timelines.getTimelines",
    "GET_TIMELINE_INFO": "Pixera.Timelines.Timeline.getTimelineInfosAsJsonString",
    "GET_CUE_INFO": "Pixera.Timelines.Timeline.getCueInfosAsJsonString",
}

# --------------------- CONFIG ---------------------
g_LogAll = True

shared_data: Dict[str, Any] = {
    "timelines": {},
    "status": {},
    "last_update": None,
    "polling": {
        "enabled": False,
        "enabled_at": None,
        "auto_disable_at": None,
    },
}
data_lock = threading.Lock()
polling_task = None
auto_disable_task = None
# Track last time project/timelines were fetched (for rate limiting in event handler)
last_event_project_timeline_fetch = 0
event_fetch_lock = threading.Lock()

MSG_TERMINATOR = "0xPX"
request_id = 1

# --------------------- LOGGING ---------------------
# Ensure logs directory exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "backend.log")

# Configure logging
logger = logging.getLogger("pixera")
logger.setLevel(logging.INFO)

# File logging (rotates at 5MB, keeps 3 old logs)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

# Console logging (for when run interactively)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

def log(message, level="info"):
    getattr(logger, level.lower())(message)

# --------------------- TIME PARSING ---------------------
def parse_countdown_string(raw: str) -> Dict[str, Any]:
    """
    Parse a countdown string "HH:MM:SS:FF" or "-HH:MM:SS:FF" into components and total milliseconds.
    Handles negative values by checking for leading minus sign.
    """
    if not raw or ":" not in raw:
        return {"raw": "", "hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "totalMs": 0}

    fps = 60
    try:
        # Check if the string starts with a negative sign
        is_negative = raw.strip().startswith("-")
        # Remove the negative sign if present for parsing
        parse_str = raw.lstrip("-") if is_negative else raw
        
        h, m, s, f = parse_str.split(":")
        hours = int(h)
        minutes = int(m)
        seconds = int(s)
        frames = int(f)

        # Calculate total milliseconds (always positive)
        totalMs = (
            hours * 3600 * 1000
            + minutes * 60 * 1000
            + seconds * 1000
            + int((frames / fps) * 1000)
        )
        
        # Apply negative sign if the original string had one
        if is_negative:
            totalMs = -totalMs
            hours = -hours  # Also negate hours for consistency
        
        return {
            "raw": raw,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "frames": frames,
            "totalMs": totalMs,
        }
    except Exception as e:
        log(f"Error parsing countdown string '{raw}': {e}", "WARN")
        return {"raw": "", "hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "totalMs": 0}
    
def buildCountdownPayload(timelines, project_name, polling_state):
    """
    Build the countdown payload shared by broadcast_update() and ws_countdowns().
    Iterates over ALL timelines and ALL valid cues to produce a flat list.
    """
    countdowns = []

    if not isinstance(timelines, dict):
        timelines = {}

    for tl_handle, tl_data in timelines.items():
        if not tl_data or not isinstance(tl_data, dict):
            continue

        info = tl_data.get("info", {}) or {}
        timeline_name = info.get("name", f"Timeline_{tl_handle}")
        timeline_mode = info.get("Mode", "BAD")

        cues = tl_data.get("cues", {}) or {}
        if not isinstance(cues, dict):
            continue

        for cue_handle, cue_data in cues.items():
            if not cue_data or not isinstance(cue_data, dict):
                continue

            # Skip if countdown is negative (hasn't started or invalid)
            original_countdown = cue_data.get("_original_countdown_ms", 0)
            if original_countdown < 0:
                continue

            cd = cue_data.get("countdown", {}) or {}
            if not isinstance(cd, dict):
                continue

            operation = cue_data.get("operation", "")

            countdowns.append({
                "id": f"{tl_handle}-{cue_handle}",
                "timelineName": timeline_name,
                "timelineMode": timeline_mode,
                "cueName": str(cue_handle),
                "cueType": operation,
                "note": cue_data.get("note", ""),
                "rawCount": cd.get("raw", ""),
                "hours": cd.get("hours", 0),
                "minutes": cd.get("minutes", 0),
                "seconds": cd.get("seconds", 0),
                "frames": cd.get("frames", 0),
                "totalMs": cd.get("totalMs", 0),
            })

    payload = {
        "projectName": project_name,
        "countdowns": countdowns,
        "polling": polling_state,
    }
    return payload
    

# --------------------- WEBSOCKET MANAGEMENT ---------------------
connected_clients: Set[WebSocket] = set()

async def broadcast_update():
    """Broadcast the current shared_data to all connected WebSocket clients."""
    if not connected_clients:
        return
    with data_lock:
        timelines = shared_data.get("timelines", {})
        project_name = shared_data.get("status", {}).get("projectName", "Unknown")
        polling_state = shared_data.get("polling", {})
    
    payload = buildCountdownPayload(timelines, project_name, polling_state)
    text = json.dumps(payload)
    to_remove = []
    for ws in connected_clients.copy():  # Use copy to avoid modification during iteration
        try:
            await ws.send_text(text)
        except (WebSocketDisconnect, RuntimeError, Exception) as e:
            # Connection closed or error - remove from set
            error_str = str(e).lower()
            if "connection" in error_str or "disconnect" in error_str or "close" in error_str:
                to_remove.append(ws)
            else:
                # Log unexpected errors but still remove the client
                log(f"Error broadcasting to WebSocket client: {e}", "WARN")
                to_remove.append(ws)
    for ws in to_remove:
        connected_clients.discard(ws)

async def broadcast_polling_state():
    """Broadcast only the polling state to all connected WebSocket clients."""
    if not connected_clients:
        return
    with data_lock:
        payload = {
            "type": "polling_state",
            "polling": shared_data["polling"],
        }
    text = json.dumps(payload)
    to_remove = []
    for ws in connected_clients.copy():  # Use copy to avoid modification during iteration
        try:
            await ws.send_text(text)
        except (WebSocketDisconnect, RuntimeError, Exception) as e:
            # Connection closed or error - remove from set
            error_str = str(e).lower()
            if "connection" in error_str or "disconnect" in error_str or "close" in error_str:
                to_remove.append(ws)
            else:
                # Log unexpected errors but still remove the client
                log(f"Error broadcasting polling state to WebSocket client: {e}", "WARN")
                to_remove.append(ws)
    for ws in to_remove:
        connected_clients.discard(ws)

# --------------------- TCP COMMUNICATION ---------------------
async def send_json(method: str, params: Dict = None) -> Dict:
    """Send JSON-RPC message over TCP and return result."""
    global request_id
    request = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params:
        request["params"] = params

    message = json.dumps(request) + MSG_TERMINATOR
    request_id += 1
    
    try:
        reader, writer = await asyncio.open_connection(PIXERA_HOST, PIXERA_PORT)
        writer.write(message.encode())
        await writer.drain()

        data = await asyncio.wait_for(reader.readuntil(MSG_TERMINATOR.encode()), timeout=3.0)
        writer.close()
        await writer.wait_closed()
        if g_LogAll:
            log(f"Sent: {message} --> {data}")

        decoded = data.decode().replace(MSG_TERMINATOR, "")
        return json.loads(decoded)
    except Exception as e:
        log(f"Error sending {method}: {e}", "WARN")
        return {}

# --------------------- PIXERA DATA RETRIEVAL ---------------------
async def get_timelines():
    result = await send_json(PIXERA_METHODS["GET_TIMELINES"])
    timelines = result.get("result", [])
    clean = {}

    for handle in timelines:
        info = await send_json(PIXERA_METHODS["GET_TIMELINE_INFO"], {"handle": handle})
        try:
            info_json = json.loads(info.get("result", "{}"))
        except Exception:
            info_json = {}

        clean[handle] = {"info": info_json, "cues": {}}

    with data_lock:
        shared_data["timelines"] = clean

    log(f"Timelines updated: {len(clean)} timelines found", "info")


async def get_cues(timeline_handle: int):
    cue_info = await send_json(PIXERA_METHODS["GET_CUE_INFO"], {"handle": timeline_handle})
    cue_data = {}
    
    result = cue_info.get("result")
    if isinstance(result, str):
        try:
            info_json = json.loads(result)
        except Exception:
            info_json = []
    else:
        info_json = result or []

    if not isinstance(info_json, list):
        info_json = []

    for cue in info_json:
        countdown_str = cue.get("countdown")
        time_str = cue.get("time")  # Final time field
        countdown_parsed = parse_countdown_string(countdown_str)
        time_parsed = parse_countdown_string(time_str) if time_str else None
        
        # Store original countdown and time values for comparison
        original_countdown_ms = countdown_parsed["totalMs"]
        original_time_ms = time_parsed["totalMs"] if time_parsed else None
        
        # If countdown is negative, use the time field value instead
        if countdown_parsed["totalMs"] < 0:
            if time_parsed and time_parsed["totalMs"] >= 0:
                # Use the time field value (which should be positive)
                countdown_parsed = time_parsed.copy()
                countdown_parsed["raw"] = countdown_str  # Keep original countdown string
            else:
                # If time field is missing or invalid, log warning and set to 0
                log(f"Warning: Cue {cue.get('name', 'unknown')} has negative countdown ({countdown_parsed['totalMs']}ms) but no valid time field. Setting to 0.", "WARN")
                countdown_parsed["totalMs"] = 0
                countdown_parsed["hours"] = 0
                countdown_parsed["minutes"] = 0
                countdown_parsed["seconds"] = 0
                countdown_parsed["frames"] = 0
        
        cue_name = cue.get("name") or cue.get("handle")

        cue_data[cue_name] = {
            **cue,
            "countdown": {
                "raw": countdown_str,
                **countdown_parsed,
            },
            # Store original values for filtering
            "_original_countdown_ms": original_countdown_ms,
            "_original_time_ms": original_time_ms,
        }

    with data_lock:
        if timeline_handle in shared_data["timelines"]:
            shared_data["timelines"][timeline_handle]["cues"] = cue_data

    log(f"Cues updated for timeline {timeline_handle}: {len(cue_data)} cues", "info")


async def get_project_name():
    result = await send_json("Pixera.Session.getProjectName")
    with data_lock:
        shared_data["status"]["projectName"] = result.get("result", "Unknown")
    log(f"Project name updated: {shared_data['status']['projectName']}", "INFO")

# --------------------- POLLING LOGIC ---------------------
async def polling_loop():
    """Poll Pixera with different intervals:
    - Project name and timelines: every 10 seconds
    - Cues: every 100ms
    """
    global polling_task, last_event_project_timeline_fetch
    log("Polling loop started.", "INFO")
    last_project_timeline_fetch = time.time()  # Track last time we fetched project/timelines
    PROJECT_TIMELINE_INTERVAL = 10.0  # 10 seconds
    
    while True:
        with data_lock:
            is_enabled = shared_data["polling"]["enabled"]
            # Get timeline handles while holding the lock
            timeline_handles = list(shared_data["timelines"].keys())
        
        if is_enabled:
            current_time = time.time()
            should_fetch_project_timelines = (current_time - last_project_timeline_fetch) >= PROJECT_TIMELINE_INTERVAL
            
            # Fetch project name and timelines every 10 seconds
            if should_fetch_project_timelines:
                await get_project_name()
                last_project_timeline_fetch = current_time
                # Sync the event handler timestamp so it knows we just fetched
                with event_fetch_lock:
                    last_event_project_timeline_fetch = current_time
                log("Fetched project name (10s interval)", "INFO")
            
            #get timeline info in case it changed mode, like play/stop/pause
            await get_timelines()
            with data_lock:
                timeline_handles = list(shared_data["timelines"].keys())
            # Always fetch cues every 100ms (using current timeline handles)
            for tl in timeline_handles:
                await get_cues(tl)
            
            # Always broadcast updates every 100ms so frontend gets frequent cue updates
            await broadcast_update()
        
        await asyncio.sleep(0.1)  # 100ms

async def auto_disable_polling():
    """Auto-disable polling after 6 hours."""
    global auto_disable_task
    await asyncio.sleep(6 * 3600)  # 6 hours in seconds
    
    with data_lock:
        if shared_data["polling"]["enabled"]:
            shared_data["polling"]["enabled"] = False
            shared_data["polling"]["enabled_at"] = None
            shared_data["polling"]["auto_disable_at"] = None
            log("Polling auto-disabled after 6 hours.", "INFO")
    
    await broadcast_polling_state()
    auto_disable_task = None

# --------------------- FASTAPI ENDPOINTS ---------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global poll_loop_started
    print(">>> ENTER LIFESPAN (should print on startup)")

    log("Starting backend initialization...", "INFO")

    # Initial data load
    await get_project_name()
    await get_timelines()
    for tl in list(shared_data["timelines"].keys()):
        await get_cues(tl)

    # Start polling loop (it will check enabled state internally)
    global polling_task
    polling_task = asyncio.create_task(polling_loop())
    log("Polling loop task started from lifespan()", "INFO")

    await broadcast_update()

    log("Backend started successfully.", "info")

    # ---- App is now running ----
    yield

    # ---- Shutdown Section (optional) ----
    log("Shutting down Pixera backend...", "INFO")

app = FastAPI(
    title="Pixera Backend API",
    version="3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def get_status():
    with data_lock:
        log(f"Send Snapshot: {shared_data}")
        return shared_data

@app.get("/api/polling/state")
async def get_polling_state():
    """Get the current polling state."""
    with data_lock:
        return shared_data["polling"]

@app.post("/api/polling/enable")
async def enable_polling():
    """Enable polling and start 6-hour auto-disable timer."""
    global polling_task, auto_disable_task
    
    with data_lock:
        if shared_data["polling"]["enabled"]:
            return {"status": "already_enabled", "polling": shared_data["polling"]}
        
        shared_data["polling"]["enabled"] = True
        shared_data["polling"]["enabled_at"] = time.time()
        shared_data["polling"]["auto_disable_at"] = time.time() + (6 * 3600)  # 6 hours from now
        
        # Start polling task if not already running
        if polling_task is None or polling_task.done():
            polling_task = asyncio.create_task(polling_loop())
            log("Polling task started.", "INFO")
        
        # Cancel existing auto-disable task if any
        if auto_disable_task and not auto_disable_task.done():
            auto_disable_task.cancel()
        
        # Start new auto-disable task
        auto_disable_task = asyncio.create_task(auto_disable_polling())
        log(f"Polling enabled. Will auto-disable at {shared_data['polling']['auto_disable_at']}", "INFO")
    
    # Immediately fetch current data and broadcast to all clients
    log("Immediately fetching current data for all clients...", "INFO")
    await get_project_name()
    await get_timelines()
    # Get timeline handles safely after get_timelines updates shared_data
    with data_lock:
        timeline_handles = list(shared_data["timelines"].keys())
    for tl in timeline_handles:
        await get_cues(tl)
    
    # Broadcast both polling state and full update to all clients
    await broadcast_polling_state()
    await broadcast_update()
    
    return {"status": "enabled", "polling": shared_data["polling"]}

@app.post("/api/polling/disable")
async def disable_polling():
    """Disable polling and cancel auto-disable timer."""
    global auto_disable_task
    
    with data_lock:
        if not shared_data["polling"]["enabled"]:
            return {"status": "already_disabled", "polling": shared_data["polling"]}
        
        shared_data["polling"]["enabled"] = False
        shared_data["polling"]["enabled_at"] = None
        shared_data["polling"]["auto_disable_at"] = None
        
        # Cancel auto-disable task
        if auto_disable_task and not auto_disable_task.done():
            auto_disable_task.cancel()
            auto_disable_task = None
        
        log("Polling disabled.", "INFO")
    
    await broadcast_polling_state()
    return {"status": "disabled", "polling": shared_data["polling"]}

@app.post("/api/force_update")
async def force_update():
    log("Force update requested via API.", "EVENT")
    await get_project_name()
    await get_timelines()
    for tl in list(shared_data["timelines"].keys()):
        await get_cues(tl)
    await broadcast_update()
    return {"status": "force updated", "timestamp": time.time()}

@app.websocket("/ws")
async def ws_countdowns(websocket: WebSocket):
    """WebSocket endpoint to send countdown updates in real-time."""
    await websocket.accept()
    connected_clients.add(websocket)
    log("Client connected to /ws", "INFO")

    try:
        # Send initial state including polling status
        try:
            with data_lock:
                timelines = shared_data.get("timelines", {})
                project_name = shared_data.get("status", {}).get("projectName", "Unknown")
                polling_state = shared_data.get("polling", {})
                
            initial_payload = buildCountdownPayload(timelines, project_name, polling_state)   
            await websocket.send_text(json.dumps(initial_payload))
            
        except WebSocketDisconnect:
            # Client disconnected before receiving initial payload; just re-raise
            log("WebSocket client disconnected while sending initial payload", "WARN")
            raise
        except Exception as e:
            log(f"Error sending initial WebSocket payload: {e}", "ERROR")
            import traceback
            log(f"Traceback: {traceback.format_exc()}", "ERROR")

        # Use a simple loop that relies on broadcast_update() for actual updates
        # This loop just keeps the connection alive and sends periodic heartbeats
        while True:
            # Check polling state to determine update frequency
            with data_lock:
                polling_state = shared_data.get("polling", {})
                is_polling = polling_state.get("enabled", False)
            
            # When polling is enabled, broadcast_update() handles the frequent updates
            # This loop just sends a heartbeat to keep connection alive
            # When polling is disabled, send updates less frequently
            if not is_polling:
                try:
                    with data_lock:
                        timelines = shared_data.get("timelines", {})
                        project_name = shared_data.get("status", {}).get("projectName", "Unknown")
                    
                    payload = buildCountdownPayload(timelines, project_name, polling_state)   
                    await websocket.send_text(json.dumps(payload))
                    await asyncio.sleep(1.0)  # 1 second when polling disabled
                except (WebSocketDisconnect, RuntimeError) as e:
                    # Connection closed - break out of loop
                    log(f"WebSocket connection closed: {e}", "WARN")
                    break
                except Exception as e:
                    # Check if it's a connection-related error
                    error_str = str(e).lower()
                    if "connection" in error_str or "disconnect" in error_str or "close" in error_str:
                        log(f"WebSocket connection error: {e}", "WARN")
                        break
                    log(f"Error in WebSocket loop (polling disabled): {e}", "ERROR")
                    import traceback
                    log(f"Traceback: {traceback.format_exc()}", "ERROR")
                    await asyncio.sleep(1.0)  # Wait before retrying
            else:
                # When polling is enabled, broadcast_update() sends updates every 100ms
                # Just wait here to avoid blocking
                try:
                    await asyncio.sleep(0.1)
                except (WebSocketDisconnect, RuntimeError) as e:
                    log(f"WebSocket connection closed: {e}", "WARN")
                    break

    except WebSocketDisconnect:
        log("Client disconnected from /ws", "WARN")
    except Exception as e:
        log(f"WebSocket error: {e}", "ERROR")
        import traceback
        log(f"WebSocket traceback: {traceback.format_exc()}", "ERROR")
    finally:
        # Always remove from connected_clients and clean up
        connected_clients.discard(websocket)
        log("WebSocket client removed from connected_clients", "INFO")
        
