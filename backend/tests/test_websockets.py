from fastapi.testclient import TestClient
from main import app
from app.websockets.manager import ws_manager

client = TestClient(app)


def test_websocket_connection_lifecycle():
    """Test WebSocket connect, initial greeting, ping/pong, and disconnect."""
    with client.websocket_connect("/api/v1/ws/events") as websocket:
        # Initial greeting message
        data = websocket.receive_json()
        assert data["type"] == "connected"

        # Ping / Pong heartbeat
        websocket.send_text("ping")
        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_broadcast(mocker):
    """Test WebSocket broadcasting to active connections."""
    with client.websocket_connect("/api/v1/ws/events") as websocket:
        # Clear initial greeting
        _ = websocket.receive_json()

        # Send broadcast from manager
        import asyncio
        test_payload = {"type": "EVENT_CREATED", "action": "created", "event": {"id": "test12345"}}
        asyncio.run(ws_manager.broadcast_json(test_payload))

        msg = websocket.receive_json()
        assert msg["type"] == "EVENT_CREATED"
        assert msg["event"]["id"] == "test12345"
