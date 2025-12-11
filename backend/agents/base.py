"""
Base Agent class for Multi-Agent Architecture
All agents inherit from this class
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import asyncio


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Each agent has a specific responsibility and can process tasks independently.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._on_message: Optional[Callable] = None
        self._on_progress: Optional[Callable] = None
    
    def set_message_handler(self, handler: Callable):
        """Set callback for sending messages during processing"""
        self._on_message = handler
    
    def set_progress_handler(self, handler: Callable):
        """Set callback for progress updates"""
        self._on_progress = handler
    
    async def send_message(self, message: str, data: Optional[Dict] = None):
        """Send a status message"""
        if self._on_message:
            await self._on_message({
                "agent": self.name,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    
    async def update_progress(self, progress: int, message: str):
        """Update progress percentage"""
        if self._on_progress:
            await self._on_progress(progress, message)
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input and return result.
        Must be implemented by subclasses.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Result dictionary with 'success' key and relevant data
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with error handling.
        """
        try:
            await self.send_message(f"{self.name} starting...")
            result = await self.process(input_data)
            
            if result.get("success"):
                await self.send_message(f"{self.name} completed successfully")
            else:
                await self.send_message(f"{self.name} failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            await self.send_message(f"{self.name} error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"
