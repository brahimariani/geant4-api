"""
WebSocket endpoints for real-time simulation streaming.
"""

import asyncio
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from app.core.simulation_engine import simulation_engine
from app.core.event_manager import event_manager
from app.models.simulation import SimulationStatus


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = []
        self.active_connections[simulation_id].append(websocket)
        logger.info(f"WebSocket connected for simulation {simulation_id}")
    
    def disconnect(self, websocket: WebSocket, simulation_id: str):
        if simulation_id in self.active_connections:
            try:
                self.active_connections[simulation_id].remove(websocket)
                if not self.active_connections[simulation_id]:
                    del self.active_connections[simulation_id]
            except ValueError:
                pass
        logger.info(f"WebSocket disconnected from simulation {simulation_id}")
    
    async def broadcast(self, simulation_id: str, message: dict):
        """Broadcast message to all connected clients for a simulation."""
        if simulation_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[simulation_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, simulation_id)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")


manager = ConnectionManager()


@router.websocket("/simulations/{simulation_id}")
async def simulation_websocket(
    websocket: WebSocket,
    simulation_id: str,
    include_hits: bool = Query(default=False),
    include_trajectories: bool = Query(default=False)
):
    """
    WebSocket endpoint for real-time simulation updates.
    
    Connect to receive:
    - Status updates
    - Progress updates (events completed, rate, ETA)
    - Event batches (optional, if include_hits=true)
    - Trajectory data (optional, if include_trajectories=true)
    - Completion notification
    - Error notifications
    
    Query parameters:
    - include_hits: Include hit data in event batches
    - include_trajectories: Include trajectory data
    
    Example connection:
    ```
    ws://localhost:8000/ws/simulations/{id}?include_hits=true
    ```
    """
    await manager.connect(websocket, simulation_id)
    
    try:
        # Check if simulation exists
        job = simulation_engine.get_simulation_status(simulation_id)
        if not job:
            await manager.send_personal(websocket, {
                "event_type": "error",
                "data": {"message": f"Simulation {simulation_id} not found"}
            })
            return
        
        # Send current status
        await manager.send_personal(websocket, {
            "event_type": "status",
            "simulation_id": simulation_id,
            "data": {
                "status": job.status.value,
                "events_completed": job.events_completed,
                "events_total": job.events_total
            }
        })
        
        # Subscribe to events
        queue = await event_manager.subscribe(simulation_id)
        
        try:
            # Listen for client messages and events
            async def receive_messages():
                while True:
                    try:
                        data = await websocket.receive_json()
                        
                        # Handle client commands
                        command = data.get("command")
                        if command == "pause":
                            await simulation_engine.pause_simulation(simulation_id)
                            await manager.send_personal(websocket, {
                                "event_type": "command_response",
                                "data": {"command": "pause", "success": True}
                            })
                        elif command == "resume":
                            await simulation_engine.resume_simulation(simulation_id)
                            await manager.send_personal(websocket, {
                                "event_type": "command_response",
                                "data": {"command": "resume", "success": True}
                            })
                        elif command == "cancel":
                            await simulation_engine.cancel_simulation(simulation_id)
                            await manager.send_personal(websocket, {
                                "event_type": "command_response",
                                "data": {"command": "cancel", "success": True}
                            })
                        elif command == "get_status":
                            job = simulation_engine.get_simulation_status(simulation_id)
                            if job:
                                await manager.send_personal(websocket, {
                                    "event_type": "status",
                                    "data": {
                                        "status": job.status.value,
                                        "events_completed": job.events_completed,
                                        "events_total": job.events_total
                                    }
                                })
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error receiving WebSocket message: {e}")
            
            async def send_events():
                while True:
                    try:
                        # Wait for event with timeout
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        
                        # Filter based on client preferences
                        if not include_hits and event.get("event_type") == "event_batch":
                            # Send without hit data
                            filtered_event = {**event}
                            if "data" in filtered_event and "sample_hits" in filtered_event["data"]:
                                del filtered_event["data"]["sample_hits"]
                            await manager.send_personal(websocket, filtered_event)
                        else:
                            await manager.send_personal(websocket, event)
                        
                        # Check if simulation completed
                        if event.get("event_type") in ["completed", "error", "cancelled"]:
                            break
                            
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        await manager.send_personal(websocket, {
                            "event_type": "heartbeat",
                            "simulation_id": simulation_id
                        })
                    except Exception as e:
                        logger.error(f"Error sending event: {e}")
                        break
            
            # Run both tasks concurrently
            receive_task = asyncio.create_task(receive_messages())
            send_task = asyncio.create_task(send_events())
            
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                
        finally:
            await event_manager.unsubscribe(simulation_id, queue)
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from simulation {simulation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_personal(websocket, {
            "event_type": "error",
            "data": {"message": str(e)}
        })
    finally:
        manager.disconnect(websocket, simulation_id)


@router.websocket("/all")
async def all_simulations_websocket(websocket: WebSocket):
    """
    WebSocket endpoint to receive updates from ALL simulations.
    
    Useful for monitoring dashboards.
    """
    await websocket.accept()
    
    try:
        queue = await event_manager.subscribe_all()
        
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({"event_type": "heartbeat"})
                    
        finally:
            await event_manager.unsubscribe("*", queue)
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from all-simulations feed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@router.get("/connections")
async def get_connections():
    """Get WebSocket connection statistics."""
    return {
        "active_simulations": list(manager.active_connections.keys()),
        "total_connections": sum(
            len(conns) for conns in manager.active_connections.values()
        ),
        "connections_by_simulation": {
            sim_id: len(conns)
            for sim_id, conns in manager.active_connections.items()
        }
    }

