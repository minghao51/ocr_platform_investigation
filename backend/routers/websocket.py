"""
WebSocket router for real-time job status updates.
"""

from cachetools import TTLCache
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from typing import Dict, Set, Optional
from database import crud
from routers.job_serialization import serialize_job
from dependencies import get_current_user
import logging
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# ── Ticket-based auth for WebSockets ────────────────────────────────────────
# Tickets are short-lived, single-use tokens exchanged for JWTs over HTTPS.
# This prevents JWTs from leaking into server logs via WebSocket URL query params.

TICKET_TTL_SECONDS = 60
TICKET_MAX_PENDING = 1000

_ticket_store: TTLCache = TTLCache(maxsize=TICKET_MAX_PENDING, ttl=TICKET_TTL_SECONDS)


def _create_ws_ticket(user_payload: dict) -> str:
    ticket = secrets.token_urlsafe(32)
    _ticket_store[ticket] = {
        "user_id": user_payload.get("user_id"),
        "is_admin": user_payload.get("is_admin", False),
    }
    return ticket


def _consume_ws_ticket(ticket: str) -> Optional[dict]:
    return _ticket_store.pop(ticket, None)


@router.post("/ws/ticket")
async def create_websocket_ticket(
    current_user: dict = Depends(get_current_user),
):
    """
    Exchange a JWT for a short-lived WebSocket ticket.

    The ticket must be used within 60 seconds and is single-use.
    Pass it as the `ticket` query parameter when connecting to the WebSocket.
    """
    ticket = _create_ws_ticket(current_user)
    return {"ticket": ticket, "expires_in": TICKET_TTL_SECONDS}


class ConnectionManager:
    """Manage WebSocket connections per job."""

    def __init__(self):
        # Map job_id -> list of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map WebSocket -> job_id (for tracking)
        self.connection_jobs: Dict[WebSocket, int] = {}

    async def connect(self, job_id: int, websocket: WebSocket) -> bool:
        """
        Connect a WebSocket to a job.

        Returns True if successful, False if job doesn't exist.
        """
        # Verify job exists
        job = await crud.get_job(job_id)
        if not job:
            return False

        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        self.connection_jobs[websocket] = job_id

        logger.info(f"WebSocket connected for job {job_id}")

        # Send current job status immediately
        await websocket.send_json(
            {
                "type": "status",
                "data": serialize_job(job),
            }
        )

        return True

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket connection."""
        job_id = self.connection_jobs.pop(websocket, None)
        if job_id and job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")

    async def broadcast_job_update(self, job_id: int, job_data: dict):
        """Broadcast job update to all connected WebSockets for this job."""
        if job_id not in self.active_connections:
            logger.debug(f"No WebSocket connections for job {job_id}")
            return

        message = {"type": "status_update", "data": job_data}

        # Remove dead connections
        dead_connections = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for connection in dead_connections:
            await self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


# Export function for other modules to call
async def broadcast_job_update(job_id: int, job_data: dict):
    """Broadcast job update to all connected WebSockets for this job."""
    await manager.broadcast_job_update(job_id, job_data)


@router.websocket("/ws/job/{job_id}")
async def job_status_websocket(
    websocket: WebSocket, job_id: int, ticket: str = Query(...)
):
    """
    WebSocket endpoint for real-time job status updates.

    Query parameters:
        ticket: Short-lived ticket obtained from POST /api/ws/ticket (required)

    Messages sent to client:
        - Initial job status on connection
        - Status updates when job changes
    """
    # Verify ticket
    payload = _consume_ws_ticket(ticket)
    if payload is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired ticket"
        )
        return

    # Verify user has access to this job
    job = await crud.get_job(job_id)
    if not job:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Job not found"
        )
        return

    # Check if user owns this job or is admin
    if job["user_id"] != payload["user_id"] and not payload.get("is_admin", False):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Access denied"
        )
        return

    # Connect WebSocket
    connected = await manager.connect(job_id, websocket)
    if not connected:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Job not found"
        )
        return

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive and ignore any messages from client
            # (we only send updates, don't receive commands)
            data = await websocket.receive_text()

            # Optionally handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
