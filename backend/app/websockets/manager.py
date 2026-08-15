import json
import logging
from typing import Any, Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("threat_atlas.websockets")


class WebSocketManager:
    """Manages active WebSocket client connections and handles broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and add to active connections pool."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("New WebSocket connection accepted. Total active: %d", len(self.active_connections))
        # Send initial connection acknowledgment
        await self.send_personal_json(websocket, {"type": "connected", "message": "Connected to ThreatAtlas real-time event stream."})

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection from active connections pool cleanly."""
        self.active_connections.discard(websocket)
        logger.info("WebSocket connection disconnected. Total active: %d", len(self.active_connections))

    async def send_personal_json(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """Send JSON payload to a specific WebSocket client."""
        try:
            await websocket.send_json(data)
        except Exception as exc:
            logger.warning("Error sending personal WS message: %s", exc)
            self.disconnect(websocket)

    async def broadcast_json(self, data: Dict[str, Any]) -> None:
        """Broadcast JSON payload to all active WebSocket clients."""
        if not self.active_connections:
            return

        disconnected: Set[WebSocket] = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception as exc:
                logger.warning("Error broadcasting WS message: %s. Disconnecting client.", exc)
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Singleton instance
ws_manager = WebSocketManager()
