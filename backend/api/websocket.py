"""
WebSocket endpoint for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

from services.task_manager import task_manager


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # task_id -> set of connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept connection and subscribe to task updates"""
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        
        # Subscribe to task updates
        async def send_update(data: dict):
            await self.send_to_task(task_id, data)
        
        task_manager.subscribe(task_id, send_update)
        
        # Send current status immediately
        task = task_manager.get_task(task_id)
        if task:
            await websocket.send_json({
                "type": "connected",
                "task_id": task_id,
                **task.to_dict()
            })
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove connection"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_to_task(self, task_id: str, data: dict):
        """Send message to all connections watching a task"""
        if task_id not in self.active_connections:
            return
        
        dead_connections = set()
        
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.active_connections[task_id].discard(conn)


# Singleton connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates.
    
    Connect to: ws://localhost:8000/ws/{task_id}
    
    Messages sent to client:
    - {"type": "connected", "task_id": "...", ...} - Initial connection
    - {"type": "progress", "task_id": "...", "phase": "...", "progress": N, ...}
    - {"type": "complete", "task_id": "...", "result": {...}}
    - {"type": "error", "task_id": "...", "error": "..."}
    """
    await manager.connect(websocket, task_id)
    
    try:
        while True:
            # Keep connection alive, handle any client messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for ping/pong
                )
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, task_id)

