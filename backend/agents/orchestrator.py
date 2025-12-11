"""
Orchestrator Agent - Coordinates all other agents
Uses Gemini for intent understanding and Veo for video generation
"""
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import asyncio
import base64

from .base import BaseAgent
from models.schemas import TaskStatus, TaskPhase
from services.gemini_service import gemini_service


class OrchestratorAgent:
    """
    Main coordinator that manages the video generation pipeline.
    Now integrated with Gemini for intelligent processing.
    """
    
    def __init__(self):
        self.name = "Orchestrator"
        self.agents: Dict[str, BaseAgent] = {}
        self._on_status_update: Optional[Callable] = None
        self._current_phase = TaskPhase.UNDERSTANDING
        self._progress = 0
        
        # Initialize Gemini service
        gemini_service.initialize()
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.name] = agent
    
    def set_status_handler(self, handler: Callable):
        """Set callback for status updates"""
        self._on_status_update = handler
    
    async def update_status(
        self, 
        phase: TaskPhase, 
        progress: int, 
        message: str,
        data: Optional[Dict] = None
    ):
        """Send status update"""
        self._current_phase = phase
        self._progress = progress
        
        if self._on_status_update:
            await self._on_status_update({
                "phase": phase.value,
                "progress": progress,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    
    async def process_video_request(
        self, 
        task_id: str,
        audio_data: Optional[str] = None,
        text_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main pipeline for processing video generation request.
        
        Flow:
        1. Understanding Phase: Parse user intent using Gemini
        2. Planning Phase: Create video script using Gemini
        3. Execution Phase: Generate video (placeholder for Phase 3)
        """
        try:
            # ============== Phase 1: Understanding ==============
            await self.update_status(
                TaskPhase.UNDERSTANDING, 
                5, 
                "Processing your input..."
            )
            
            # Get the input text
            user_input = text_input
            
            # If audio data is provided, transcribe it
            if audio_data and not text_input:
                await self.update_status(
                    TaskPhase.UNDERSTANDING, 
                    10, 
                    "Transcribing your voice with AI..."
                )
                user_input = await self._transcribe_audio(audio_data)
                
                if user_input:
                    await self.update_status(
                        TaskPhase.UNDERSTANDING, 
                        15, 
                        f"Heard: \"{user_input[:80]}{'...' if len(user_input) > 80 else ''}\"",
                        data={"transcription": user_input}
                    )
            
            if not user_input:
                error_msg = "Could not understand audio. Please try speaking more clearly or use text input."
                await self.update_status(
                    TaskPhase.UNDERSTANDING,
                    0,
                    error_msg
                )
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": error_msg
                }
            
            await self.update_status(
                TaskPhase.UNDERSTANDING, 
                20, 
                "Analyzing your request with AI..."
            )
            
            # Use Gemini to understand intent
            intent = await gemini_service.understand_intent(user_input)
            
            # Safely extract intent values
            topic = intent.get('topic') or 'your topic'
            video_type = intent.get('video_type') or 'video'
            duration = intent.get('duration') or 8
            
            await self.update_status(
                TaskPhase.UNDERSTANDING, 
                35, 
                f"Understood: Creating a {duration}s {video_type} about {topic[:50]}"
            )
            
            # ============== Phase 2: Planning ==============
            await self.update_status(
                TaskPhase.PLANNING, 
                40, 
                "Creating optimized video prompt..."
            )
            
            # Use Gemini to create video prompt
            video_prompt = await gemini_service.generate_video_prompt(intent)
            
            if not video_prompt:
                video_prompt = f"A cinematic video about {topic}"
            
            await self.update_status(
                TaskPhase.PLANNING, 
                55, 
                f"Video prompt ready: {video_prompt[:60]}..."
            )
            
            # ============== Phase 3: Execution ==============
            await self.update_status(
                TaskPhase.EXECUTION, 
                60, 
                "Starting video generation with Veo 2... (this may take 1-3 minutes)"
            )
            
            # Progress callback for video generation
            async def on_video_progress(progress: int, message: str):
                await self.update_status(TaskPhase.EXECUTION, progress, message)
            
            # Generate video using Veo
            video_path = await gemini_service.generate_video(
                prompt=video_prompt,
                task_id=task_id,
                on_progress=on_video_progress
            )
            
            video_url = None
            if video_path:
                video_url = gemini_service.get_video_url(task_id)
                await self.update_status(
                    TaskPhase.EXECUTION, 
                    95, 
                    "Video generated successfully!"
                )
            else:
                await self.update_status(
                    TaskPhase.EXECUTION, 
                    95, 
                    "Video generation failed. Your API may not have Veo access."
                )
            
            # ============== Complete ==============
            await self.update_status(
                TaskPhase.COMPLETED, 
                100, 
                "Video generation complete!" if video_url else "Process completed!"
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "intent": intent,
                "video_prompt": video_prompt,
                "video_url": video_url,
                "message": "Video generation pipeline completed successfully"
            }
            
        except Exception as e:
            await self.update_status(
                self._current_phase,
                self._progress,
                f"Error: {str(e)}"
            )
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    async def _transcribe_audio(self, audio_base64: str) -> str:
        """
        Transcribe audio to text using Gemini multimodal.
        """
        try:
            # Use Gemini for transcription
            transcription = await gemini_service.transcribe_audio(audio_base64)
            
            if transcription and len(transcription.strip()) > 0:
                return transcription.strip()
            else:
                print("Transcription returned empty, audio may be too short or unclear")
                
        except Exception as e:
            print(f"Audio transcription failed: {e}")
        
        # If transcription fails, return None to indicate failure
        # The caller will handle this appropriately
        return ""


# Singleton instance
orchestrator = OrchestratorAgent()
