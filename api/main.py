import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import fetch_recent_incidents, fetch_incident_by_id, fetch_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: str):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

async def poll_loop():
    interval = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    seen_ids = set()
    log.info("Poll loop started, interval=%ds", interval)

    while True:
        try:
            rows = fetch_recent_incidents(limit=50)
            for row in rows:
                iid = row["incident_id"]
                if iid not in seen_ids:
                    seen_ids.add(iid)
                    await manager.broadcast(json.dumps(row, default=str))
        except Exception as e:
            log.error("Poll error: %s", e)
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_loop())
    yield                        # API is running
    task.cancel()                # shutdown

app = FastAPI(title="SRE Incident Intelligence API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # we'll tighten this to your Vercel URL later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}

@app.get("/incidents")
def list_incidents(
    limit: int = Query(default=50, le=200),
    severity: str | None = Query(default=None),
):
    return {"incidents": fetch_recent_incidents(limit=limit, severity=severity)}

@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    row = fetch_incident_by_id(incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return row

@app.get("/stats")
def stats():
    return fetch_stats()

@app.websocket("/ws/incidents")
async def ws_incidents(websocket: WebSocket):
    await manager.connect(websocket)
    log.info("Client connected, total=%d", len(manager.active))
    try:
        # Send the last 20 incidents immediately so the client isn't staring at blank screen
        for row in fetch_recent_incidents(limit=20):
            await websocket.send_text(json.dumps(row, default=str))
        while True:
            await websocket.receive_text()  # keeps the connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        log.info("Client disconnected, total=%d", len(manager.active))