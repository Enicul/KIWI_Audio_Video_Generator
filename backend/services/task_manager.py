"""
Simple Task Manager - No complex dependencies
Uses in-memory storage and asyncio for task execution
"""
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import asyncio
import uuid

from models.schemas import TaskStatus, TaskPhase


class Task:
    """Simple task representation"""
    
    def __init__(self, task_id: str, input_data: Dict[str, Any]):
        self.id = task_id
        self.input_data = input_data
        self.status = TaskStatus.PENDING
        self.phase = TaskPhase.UNDERSTANDING
        self.progress = 0
        self.message = "Task created"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.id,
            "status": self.status.value,
            "phase": self.phase.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TaskManager:
    """
    Simple in-memory task manager.
    Manages task lifecycle and provides updates via callbacks.
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._status_handlers: Dict[str, List[Callable]] = {}  # task_id -> handlers
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """Create a new task"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, input_data)
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        phase: Optional[TaskPhase] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update task state"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        if status is not None:
            task.status = status
        if phase is not None:
            task.phase = phase
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        
        task.updated_at = datetime.now()
    
    def subscribe(self, task_id: str, handler: Callable):
        """Subscribe to task updates"""
        if task_id not in self._status_handlers:
            self._status_handlers[task_id] = []
        self._status_handlers[task_id].append(handler)
    
    def unsubscribe(self, task_id: str, handler: Callable):
        """Unsubscribe from task updates"""
        if task_id in self._status_handlers:
            try:
                self._status_handlers[task_id].remove(handler)
            except ValueError:
                pass
    
    async def notify_subscribers(self, task_id: str, data: Dict[str, Any]):
        """Notify all subscribers of task updates"""
        handlers = self._status_handlers.get(task_id, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
    
    async def run_task(self, task_id: str, processor: Callable) -> Dict[str, Any]:
        """
        Run a task with the given processor function.
        The processor should be an async function.
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        # Update status
        self.update_task(task_id, status=TaskStatus.PROCESSING)
        
        try:
            # Create status update callback
            async def on_status_update(update: Dict[str, Any]):
                phase = TaskPhase(update.get("phase", "understanding"))
                self.update_task(
                    task_id,
                    phase=phase,
                    progress=update.get("progress", 0),
                    message=update.get("message", "")
                )
                # Notify WebSocket subscribers
                await self.notify_subscribers(task_id, {
                    "type": "progress",
                    "task_id": task_id,
                    **task.to_dict()
                })
            
            # Run the processor
            result = await processor(on_status_update)
            
            # Update final status
            if result.get("success"):
                self.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    phase=TaskPhase.COMPLETED,
                    progress=100,
                    message="Completed successfully",
                    result=result
                )
            else:
                self.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error=result.get("error", "Unknown error")
                )
            
            # Final notification
            await self.notify_subscribers(task_id, {
                "type": "complete" if result.get("success") else "error",
                "task_id": task_id,
                **task.to_dict()
            })
            
            return result
            
        except Exception as e:
            self.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
            await self.notify_subscribers(task_id, {
                "type": "error",
                "task_id": task_id,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    def start_task_async(self, task_id: str, processor: Callable):
        """Start a task in the background"""
        async_task = asyncio.create_task(self.run_task(task_id, processor))
        self._running_tasks[task_id] = async_task
        return async_task
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks as dictionaries"""
        return [task.to_dict() for task in self.tasks.values()]


# Singleton instance
task_manager = TaskManager()

