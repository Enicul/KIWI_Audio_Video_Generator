"""
Orchestrator Agent - Coordinates all agents in Multi-Agent Architecture
Supports both single-scene and multi-scene video generation
"""
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import os

from google import genai

from .base import BaseAgent
from .speech_agent import speech_agent
from .clarification_agent import clarification_agent
from .intent_agent import intent_agent
from .script_analyzer_agent import script_analyzer_agent
from .prompt_agent import prompt_agent
from .video_agent import video_agent
from .video_stitch_agent import video_stitch_agent
from models.schemas import TaskPhase


class OrchestratorAgent(BaseAgent):
    """
    Master agent coordinating the video generation pipeline.
    
    Single-scene: SpeechAgent → IntentAgent → PromptAgent → VideoAgent
    Multi-scene:  SpeechAgent → IntentAgent → ScriptAnalyzerAgent 
                  → [PromptAgent → VideoAgent] × N → VideoStitchAgent
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
            clarification_agent.initialize(self.client)
            intent_agent.initialize(self.client)
            script_analyzer_agent.initialize(self.client)
            prompt_agent.initialize(self.client)
            video_agent.initialize(self.client, self.api_key)
            # video_stitch_agent doesn't need client
            self._initialized = True
            print("✓ Orchestrator initialized with 7 agents")
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
        """Main pipeline with multi-scene support"""
        try:
            transcription = ""
            
            # ========== Step 1: Speech to Text ==========
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
                TaskPhase.UNDERSTANDING, 15, f"Heard: \"{transcription[:60]}...\"",
                data={"transcription": transcription}
            )
            
            # ========== Step 2: Intent Analysis ==========
            await self.update_status(TaskPhase.UNDERSTANDING, 20, "IntentAgent analyzing...")
            
            result = await intent_agent.run({"text": transcription})
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Intent failed")}
            intent = result.get("intent", {})
            
            await self.update_status(TaskPhase.UNDERSTANDING, 25, f"Intent: {intent.get('video_type', 'video')}")
            
            # ========== Step 3: Script Analysis (Multi-scene detection) ==========
            await self.update_status(TaskPhase.PLANNING, 30, "ScriptAnalyzerAgent analyzing structure...")
            
            async def script_progress(p, m): await self.update_status(TaskPhase.PLANNING, p, m)
            script_analyzer_agent.set_progress_handler(script_progress)
            
            result = await script_analyzer_agent.run({
                "text": transcription,
                "intent": intent
            })
            
            if not result.get("success"):
                # Fallback to single scene
                scenes = [{"scene_number": 1, "description": transcription, "title": "Main Scene"}]
                is_multi_scene = False
            else:
                scenes = result.get("scenes", [])
                is_multi_scene = result.get("is_multi_scene", False)
            
            total_scenes = len(scenes)
            
            if is_multi_scene:
                await self.update_status(
                    TaskPhase.PLANNING, 35, 
                    f"📽️ Multi-scene story detected: {total_scenes} scenes",
                    data={"scenes": scenes, "is_multi_scene": True}
                )
            else:
                await self.update_status(TaskPhase.PLANNING, 35, "Single scene video")
            
            # ========== Step 4: Generate Videos ==========
            video_paths = []
            video_prompts = []
            
            for i, scene in enumerate(scenes):
                scene_num = i + 1
                scene_desc = scene.get("description", scene.get("title", f"Scene {scene_num}"))
                
                # Calculate progress for this scene
                # Each scene gets equal portion of 40-90 range
                scene_progress_start = 40 + int((i / total_scenes) * 50)
                scene_progress_end = 40 + int(((i + 1) / total_scenes) * 50)
                
                # 4a: Generate prompt for this scene
                await self.update_status(
                    TaskPhase.EXECUTION, 
                    scene_progress_start, 
                    f"Scene {scene_num}/{total_scenes}: Creating prompt..."
                )
                
                # Create scene-specific intent
                scene_intent = {
                    **intent,
                    "topic": scene_desc,
                    "original_input": scene_desc,
                    "scene_number": scene_num,
                    "total_scenes": total_scenes
                }
                
                result = await prompt_agent.run({"intent": scene_intent})
                if not result.get("success"):
                    video_prompts.append(f"Scene {scene_num}: {scene_desc}")
                else:
                    video_prompts.append(result.get("prompt", scene_desc))
                
                # 4b: Generate video for this scene
                scene_task_id = f"{task_id}_scene{scene_num}"
                
                await self.update_status(
                    TaskPhase.EXECUTION,
                    scene_progress_start + 5,
                    f"Scene {scene_num}/{total_scenes}: Generating video with Veo 2..."
                )
                
                # Progress callback for video generation
                async def video_progress(p, m):
                    # Map video progress (60-90) to scene's progress range
                    mapped_progress = scene_progress_start + int((p - 60) / 30 * (scene_progress_end - scene_progress_start))
                    await self.update_status(
                        TaskPhase.EXECUTION, 
                        mapped_progress, 
                        f"Scene {scene_num}/{total_scenes}: {m}"
                    )
                
                video_agent.set_progress_handler(video_progress)
                
                result = await video_agent.run({
                    "prompt": video_prompts[-1],
                    "task_id": scene_task_id
                })
                
                if result.get("success") and result.get("video_path"):
                    video_paths.append(result.get("video_path"))
                    await self.update_status(
                        TaskPhase.EXECUTION,
                        scene_progress_end,
                        f"Scene {scene_num}/{total_scenes}: ✓ Complete"
                    )
                else:
                    print(f"Scene {scene_num} generation failed: {result.get('error')}")
                    # Continue with other scenes
            
            # ========== Step 5: Stitch Videos (if multi-scene) ==========
            if len(video_paths) == 0:
                return {
                    "success": False,
                    "error": "No videos were generated successfully",
                    "transcription": transcription
                }
            
            if len(video_paths) > 1:
                await self.update_status(TaskPhase.EXECUTION, 92, f"Stitching {len(video_paths)} scenes together...")
                
                async def stitch_progress(p, m): await self.update_status(TaskPhase.EXECUTION, p, m)
                video_stitch_agent.set_progress_handler(stitch_progress)
                
                result = await video_stitch_agent.run({
                    "video_paths": video_paths,
                    "task_id": task_id
                })
                
                if result.get("success"):
                    video_url = result.get("video_url")
                else:
                    # Fallback to first video
                    video_url = f"/api/video/file/{task_id}_scene1.mp4"
            else:
                # Single video
                video_url = f"/api/video/file/{task_id}_scene1.mp4" if is_multi_scene else f"/api/video/file/{task_id}.mp4"
            
            # ========== Complete ==========
            await self.update_status(TaskPhase.COMPLETED, 100, 
                f"✨ {'Multi-scene video' if is_multi_scene else 'Video'} generation complete!"
            )
            
            return {
                "success": True,
                "video_url": video_url,
                "video_prompt": "\n\n".join([f"Scene {i+1}: {p}" for i, p in enumerate(video_prompts)]) if is_multi_scene else video_prompts[0] if video_prompts else "",
                "transcription": transcription,
                "intent": intent,
                "is_multi_scene": is_multi_scene,
                "total_scenes": total_scenes,
                "scenes_generated": len(video_paths)
            }
            
        except Exception as e:
            print(f"Orchestrator error: {e}")
            return {"success": False, "error": str(e)}


orchestrator = OrchestratorAgent()
