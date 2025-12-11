"""
Orchestrator Agent - Coordinates all agents in Multi-Agent Architecture
"""
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import os

from google import genai

from .base import BaseAgent
from .speech_agent import speech_agent
from .intent_agent import intent_agent
from .prompt_agent import prompt_agent
from .video_agent import video_agent
from models.schemas import TaskPhase


class OrchestratorAgent(BaseAgent):
    """
    Master agent coordinating the video generation pipeline.
    Pipeline: SpeechAgent → IntentAgent → PromptAgent → VideoAgent
    """
    
    def __init__(self):
        super().__init__(name="Orchestrator", description="Coordinates all agents")
        self._status_callback: Optional[Callable] = None
        self._initialized = False
        self.client = None
        self.api_key = None
    
    def initialize(self, api_key: Optional[str] = None):
        """Initialize all agents"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("Warning: No API key. Agents in fallback mode.")
            return False
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            speech_agent.initialize(self.client)
            intent_agent.initialize(self.client)
            prompt_agent.initialize(self.client)
            video_agent.initialize(self.client, self.api_key)
            self._initialized = True
            print("✓ Orchestrator initialized with 4 agents")
            return True
        except Exception as e:
            print(f"Failed to initialize: {e}")
            return False
    
    def set_status_handler(self, handler: Callable):
        self._status_callback = handler
    
    async def update_status(self, phase: TaskPhase, progress: int, message: str, data: Optional[Dict] = None):
        if self._status_callback:
            await self._status_callback({
                "phase": phase.value, "progress": progress, 
                "message": message, "data": data or {}
            })
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.process_video_request(
            input_data.get("task_id", ""),
            input_data.get("audio_data"),
            input_data.get("text_input")
        )
    
    async def process_video_request(
        self, task_id: str, audio_data: Optional[str] = None, text_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pipeline: Audio → Text → Intent → Prompt → Video"""
        try:
            transcription = ""
            
            # Step 1: SpeechAgent
            if audio_data:
                await self.update_status(TaskPhase.UNDERSTANDING, 5, "SpeechAgent processing...")
                
                async def progress_cb(p, m): await self.update_status(TaskPhase.UNDERSTANDING, p, m)
                speech_agent.set_progress_handler(progress_cb)
                
                result = await speech_agent.run({"audio_data": audio_data})
                if not result.get("success"):
                    return {"success": False, "error": result.get("error", "Speech failed")}
                transcription = result.get("transcription", "")
            else:
                transcription = text_input or ""
            
            if not transcription:
                await self.update_status(TaskPhase.UNDERSTANDING, 0, "No input detected")
                return {"success": False, "error": "No transcription"}
            
            await self.update_status(
                TaskPhase.UNDERSTANDING, 20, f"Heard: \"{transcription[:60]}...\"",
                data={"transcription": transcription}
            )
            
            # Step 2: IntentAgent
            await self.update_status(TaskPhase.UNDERSTANDING, 25, "IntentAgent analyzing...")
            
            async def intent_progress(p, m): await self.update_status(TaskPhase.UNDERSTANDING, p, m)
            intent_agent.set_progress_handler(intent_progress)
            
            result = await intent_agent.run({"text": transcription})
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Intent failed")}
            intent = result.get("intent", {})
            
            await self.update_status(TaskPhase.UNDERSTANDING, 35, f"Intent: {intent.get('video_type')} about {intent.get('topic', '')[:30]}")
            
            # Step 3: PromptAgent
            await self.update_status(TaskPhase.PLANNING, 40, "PromptAgent creating prompt...")
            
            async def prompt_progress(p, m): await self.update_status(TaskPhase.PLANNING, p, m)
            prompt_agent.set_progress_handler(prompt_progress)
            
            result = await prompt_agent.run({"intent": intent})
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Prompt failed")}
            video_prompt = result.get("prompt", "")
            
            await self.update_status(TaskPhase.PLANNING, 55, f"Prompt: {video_prompt[:50]}...")
            
            # Step 4: VideoAgent
            await self.update_status(TaskPhase.EXECUTION, 60, "VideoAgent starting Veo 2...")
            
            async def video_progress(p, m): await self.update_status(TaskPhase.EXECUTION, p, m)
            video_agent.set_progress_handler(video_progress)
            
            result = await video_agent.run({"prompt": video_prompt, "task_id": task_id})
            
            video_url = result.get("video_url") if result.get("success") else None
            
            await self.update_status(TaskPhase.COMPLETED, 100, "All agents completed!")
            
            return {
                "success": True, "video_url": video_url, "video_prompt": video_prompt,
                "transcription": transcription, "intent": intent
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


orchestrator = OrchestratorAgent()
