"""
Multi-Agent Architecture for KIWI-Video

Agents:
- SpeechAgent: Audio → Text transcription
- ClarificationAgent: Multi-turn dialog for intent clarification
- IntentAgent: Text → User intent analysis  
- ScriptAnalyzerAgent: Analyzes and segments scripts into scenes
- PromptAgent: Intent → Video prompt generation
- VideoAgent: Prompt → Video generation with Veo 2
- VideoStitchAgent: Concatenates multiple videos
- Orchestrator: Coordinates all agents
"""
from .base import BaseAgent
from .speech_agent import speech_agent, SpeechAgent
from .clarification_agent import clarification_agent, ClarificationAgent
from .intent_agent import intent_agent, IntentAgent
from .script_analyzer_agent import script_analyzer_agent, ScriptAnalyzerAgent
from .prompt_agent import prompt_agent, PromptAgent
from .video_agent import video_agent, VideoAgent
from .video_stitch_agent import video_stitch_agent, VideoStitchAgent
from .orchestrator import orchestrator, OrchestratorAgent

__all__ = [
    "BaseAgent",
    "SpeechAgent", "speech_agent",
    "ClarificationAgent", "clarification_agent",
    "IntentAgent", "intent_agent",
    "ScriptAnalyzerAgent", "script_analyzer_agent",
    "PromptAgent", "prompt_agent",
    "VideoAgent", "video_agent",
    "VideoStitchAgent", "video_stitch_agent",
    "OrchestratorAgent", "orchestrator"
]
