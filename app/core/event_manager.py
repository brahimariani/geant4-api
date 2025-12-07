"""
Event manager for handling simulation events and callbacks.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from loguru import logger
import json


class EventManager:
    """
    Manages event subscriptions and broadcasting for real-time updates.
    
    Supports:
    - WebSocket client subscriptions
    - Event filtering by type and simulation
    - Buffered event history
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self, 
        simulation_id: str,
        event_types: Optional[List[str]] = None
    ) -> asyncio.Queue:
        """
        Subscribe to events for a simulation.
        
        Returns a queue that will receive events.
        """
        queue: asyncio.Queue = asyncio.Queue()
        
        async with self._lock:
            if simulation_id not in self._subscribers:
                self._subscribers[simulation_id] = []
            self._subscribers[simulation_id].append(queue)
        
        logger.debug(f"New subscriber for simulation {simulation_id}")
        return queue
    
    async def unsubscribe(self, simulation_id: str, queue: asyncio.Queue):
        """Unsubscribe from simulation events."""
        async with self._lock:
            if simulation_id in self._subscribers:
                try:
                    self._subscribers[simulation_id].remove(queue)
                    if not self._subscribers[simulation_id]:
                        del self._subscribers[simulation_id]
                except ValueError:
                    pass
        
        logger.debug(f"Unsubscribed from simulation {simulation_id}")
    
    async def publish(
        self, 
        simulation_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ):
        """
        Publish an event to all subscribers.
        """
        event = {
            "simulation_id": simulation_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        # Broadcast to subscribers
        if simulation_id in self._subscribers:
            for queue in self._subscribers[simulation_id]:
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.error(f"Error publishing event: {e}")
        
        # Also broadcast to global subscribers
        if "*" in self._subscribers:
            for queue in self._subscribers["*"]:
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.error(f"Error publishing to global subscriber: {e}")
    
    async def subscribe_all(self) -> asyncio.Queue:
        """Subscribe to events from all simulations."""
        return await self.subscribe("*")
    
    def get_history(
        self, 
        simulation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event history with optional filtering.
        """
        events = self._event_history
        
        if simulation_id:
            events = [e for e in events if e["simulation_id"] == simulation_id]
        
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        return events[-limit:]
    
    def clear_history(self, simulation_id: Optional[str] = None):
        """Clear event history."""
        if simulation_id:
            self._event_history = [
                e for e in self._event_history 
                if e["simulation_id"] != simulation_id
            ]
        else:
            self._event_history.clear()
    
    def get_subscriber_count(self, simulation_id: Optional[str] = None) -> int:
        """Get number of active subscribers."""
        if simulation_id:
            return len(self._subscribers.get(simulation_id, []))
        return sum(len(subs) for subs in self._subscribers.values())


# Global event manager instance
event_manager = EventManager()

