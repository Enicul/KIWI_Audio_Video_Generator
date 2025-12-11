"""
Base Agent class - Simple and straightforward
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import asyncio


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Keep it simple - each agent has a name and can process tasks.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._on_message: Optional[Callable] = None
    
    def set_message_handler(self, handler: Callable):
        """Set callback for sending messages during processing"""
        self._on_message = handler
    
    async def send_message(self, message: str, data: Optional[Dict] = None):
        """Send a status message"""
        if self._on_message:
            await self._on_message({
                "agent": self.name,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input and return result.
        Must be implemented by subclasses.
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with error handling.
        """
        try:
            await self.send_message(f"Starting {self.name}...")
            result = await self.process(input_data)
            await self.send_message(f"{self.name} completed successfully")
            return {"success": True, "data": result}
        except Exception as e:
            await self.send_message(f"{self.name} failed: {str(e)}")
            return {"success": False, "error": str(e)}

