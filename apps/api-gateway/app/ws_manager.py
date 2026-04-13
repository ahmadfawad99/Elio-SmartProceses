"""
WebSocket connection manager.
Maintains a pool of active WebSocket connections and broadcasts messages to all of them.
"""
from __future__ import annotations

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("WebSocket connected. Total: %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("WebSocket disconnected. Total: %d", len(self._connections))

    async def send(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as exc:
            logger.warning("Failed to send to WebSocket: %s", exc)
            self.disconnect(websocket)

    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return
        
        logger.info(f"Broadcasting {message.get('type')} to {len(self._connections)} clients")
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning("Broadcast failed for a connection: %s", exc)
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
