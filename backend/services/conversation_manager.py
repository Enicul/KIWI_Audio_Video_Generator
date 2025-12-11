"""
Conversation Manager - Manages multi-turn dialog state
Stores conversation history and accumulated intent
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class ConversationState(str, Enum):
    """Conversation states"""
    ACTIVE = "active"           # Ongoing conversation
    CLARIFYING = "clarifying"   # Waiting for user clarification
    CONFIRMED = "confirmed"     # User confirmed, ready to generate
    GENERATING = "generating"   # Video generation in progress
    COMPLETED = "completed"     # Video generated
    CANCELLED = "cancelled"     # User cancelled


class Message:
    """Single message in conversation"""
    
    def __init__(self, role: str, content: str, msg_type: str = "text"):
        self.id = str(uuid.uuid4())
        self.role = role  # "user" or "assistant"
        self.content = content
        self.msg_type = msg_type  # "text", "audio", "video"
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "type": self.msg_type,
            "timestamp": self.timestamp.isoformat()
        }


class Conversation:
    """Single conversation session"""
    
    def __init__(self, conversation_id: str):
        self.id = conversation_id
        self.state = ConversationState.ACTIVE
        self.messages: List[Message] = []
        self.accumulated_intent: Dict[str, Any] = {}
        self.pending_questions: List[str] = []
        self.task_id: Optional[str] = None  # Associated video task
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(self, role: str, content: str, msg_type: str = "text") -> Message:
        """Add a message to the conversation"""
        message = Message(role, content, msg_type)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def update_intent(self, intent: Dict[str, Any]):
        """Update accumulated intent"""
        for key, value in intent.items():
            if value is not None:
                self.accumulated_intent[key] = value
        self.updated_at = datetime.now()
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get message history"""
        return [msg.to_dict() for msg in self.messages[-limit:]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.id,
            "state": self.state.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "accumulated_intent": self.accumulated_intent,
            "pending_questions": self.pending_questions,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConversationManager:
    """
    Manages all conversation sessions.
    In-memory storage (can be extended to Redis/DB).
    """
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
    
    def create_conversation(self) -> Conversation:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(conversation_id)
        self.conversations[conversation_id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_or_create(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing or create new conversation"""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        return self.create_conversation()
    
    def update_state(self, conversation_id: str, state: ConversationState):
        """Update conversation state"""
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.state = state
            conv.updated_at = datetime.now()
    
    def set_task_id(self, conversation_id: str, task_id: str):
        """Associate a task with conversation"""
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.task_id = task_id
            conv.updated_at = datetime.now()
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations"""
        return [conv.to_dict() for conv in self.conversations.values()]


# Singleton instance
conversation_manager = ConversationManager()

