import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import ws_manager

logger = logging.getLogger("threat_atlas.api.websockets")

router = APIRouter()


@router.websocket("/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint streaming live intelligence events:
    WS /api/v1/ws/events
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain connection and listen for client ping / messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket connection exception: %s", exc)
        ws_manager.disconnect(websocket)
