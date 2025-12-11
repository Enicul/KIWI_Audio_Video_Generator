"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPhase(str, Enum):
    """Task processing phase"""
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    EXECUTION = "execution"
    COMPLETED = "completed"


# ============== Request Schemas ==============

class VideoRequest(BaseModel):
    """Request to create a video from voice/text"""
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    text_input: Optional[str] = Field(None, description="Text input if no audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text_input": "Create a 30-second promotional video about AI technology"
            }
        }


# ============== Response Schemas ==============

class TaskResponse(BaseModel):
    """Response after creating a task"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(default_factory=datetime.now)


class TaskStatusResponse(BaseModel):
    """Response for task status query"""
    task_id: str
    status: TaskStatus
    phase: TaskPhase
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentMessage(BaseModel):
    """Message from an agent during processing"""
    agent_name: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============== WebSocket Schemas ==============

class WSMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type: status, progress, result, error")
    task_id: str
    payload: Dict[str, Any]


# ============== Internal Schemas ==============

class VideoIntent(BaseModel):
    """Parsed video intent from user input"""
    topic: str = Field(..., description="Main topic or subject")
    video_type: str = Field("short video", description="Type: promotional, educational, story, etc.")
    style: str = Field("cinematic", description="Visual style")
    mood: str = Field("engaging", description="Emotional tone")
    duration: int = Field(8, description="Target duration in seconds (max 8 for Veo)")
    key_elements: List[str] = Field(default_factory=list, description="Important visual elements")
    original_input: Optional[str] = None


# ============== Conversation Schemas ==============

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    msg_type: str = Field("text", description="text, audio, or system")


class ConversationRequest(BaseModel):
    """Request to send a message in conversation"""
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    message: Optional[str] = Field(None, description="Text message")
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio")
    confirm_generate: bool = Field(False, description="User confirms to start generation")


class ConversationResponse(BaseModel):
    """Response from conversation endpoint"""
    conversation_id: str
    state: str
    ai_response: str
    needs_clarification: bool
    questions: List[str] = []
    accumulated_intent: Dict[str, Any] = {}
    ready_to_generate: bool = False
    task_id: Optional[str] = None
    messages: List[Dict[str, Any]] = []

