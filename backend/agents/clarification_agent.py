"""
Clarification Agent - Analyzes user intent and asks clarifying questions
Ensures complete understanding before video generation
"""
from typing import Any, Dict, List, Optional
import json

from .base import BaseAgent


class ClarificationAgent(BaseAgent):
    """
    Agent responsible for analyzing user input completeness.
    Generates clarifying questions when information is missing.
    """
    
    # Required fields for complete video intent
    REQUIRED_FIELDS = [
        ("topic", "What is the main subject/topic of the video?"),
        ("style", "What visual style do you prefer? (cinematic, cartoon, realistic, etc.)"),
        ("duration", "How long should the video be?"),
        ("mood", "What mood/atmosphere should the video have?"),
    ]
    
    def __init__(self):
        super().__init__(
            name="ClarificationAgent",
            description="Analyzes intent completeness and generates clarifying questions"
        )
        self.client = None
        self._initialized = False
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user input and determine if clarification is needed.
        
        Input:
            text: User's current message
            conversation_history: List of previous messages
            current_intent: Accumulated intent from conversation
            
        Output:
            success: bool
            needs_clarification: bool
            questions: List[str] (if clarification needed)
            updated_intent: Dict (accumulated intent)
            ready_to_generate: bool
        """
        text = input_data.get("text", "")
        history = input_data.get("conversation_history", [])
        current_intent = input_data.get("current_intent", {})
        
        if not text:
            return {"success": False, "error": "No input provided"}
        
        if not self._initialized or not self.client:
            # Fallback: simple keyword analysis
            return self._fallback_analysis(text, current_intent)
        
        try:
            # Build conversation context
            context = self._build_context(history)
            
            # Use Gemini to analyze
            prompt = f"""You are analyzing a user's video creation request to determine if we have enough information.

Previous conversation:
{context}

Current user message: "{text}"

Current accumulated intent:
{json.dumps(current_intent, indent=2) if current_intent else "None yet"}

Analyze whether we have complete information to create a video. We need:
1. Topic/Subject - What the video is about (REQUIRED)
2. Style - Visual style (cinematic, cartoon, anime, realistic, etc.)
3. Duration - Video length (default: 8 seconds if not specified)
4. Mood - Atmosphere (exciting, calm, dramatic, funny, etc.)
5. Key elements - Specific things to include

Rules:
- If the user explicitly says "generate", "create now", "let's do it", "确认", "开始生成" etc., set ready_to_generate to true
- If topic is clear, we can proceed with reasonable defaults for other fields
- Only ask 1-2 questions at a time, not all at once
- Be conversational and friendly

Return a JSON object:
{{
    "updated_intent": {{
        "topic": "extracted topic or null",
        "style": "extracted style or null", 
        "duration": number or null,
        "mood": "extracted mood or null",
        "key_elements": ["list", "of", "elements"],
        "original_input": "accumulated user input"
    }},
    "needs_clarification": true/false,
    "questions": ["question1", "question2"] or [],
    "ready_to_generate": true/false,
    "ai_response": "friendly response to user"
}}

Return ONLY valid JSON, no markdown."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response or not response.text:
                return self._fallback_analysis(text, current_intent)
            
            # Parse response
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text.strip())
            
            # Merge with current intent
            updated_intent = result.get("updated_intent", {})
            for key, value in current_intent.items():
                if key not in updated_intent or updated_intent[key] is None:
                    updated_intent[key] = value
            
            # Accumulate original input
            prev_input = current_intent.get("original_input", "")
            new_input = text
            updated_intent["original_input"] = f"{prev_input} {new_input}".strip()
            
            return {
                "success": True,
                "needs_clarification": result.get("needs_clarification", False),
                "questions": result.get("questions", []),
                "updated_intent": updated_intent,
                "ready_to_generate": result.get("ready_to_generate", False),
                "ai_response": result.get("ai_response", "")
            }
            
        except Exception as e:
            print(f"Clarification analysis failed: {e}")
            return self._fallback_analysis(text, current_intent)
    
    def _build_context(self, history: List[Dict]) -> str:
        """Build conversation context string"""
        if not history:
            return "No previous conversation"
        
        lines = []
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role.upper()}: {content}")
        
        return "\n".join(lines)
    
    def _fallback_analysis(self, text: str, current_intent: Dict) -> Dict[str, Any]:
        """Simple fallback analysis without API"""
        # Check for confirmation keywords
        confirm_keywords = ["generate", "create", "go", "yes", "确认", "开始", "生成", "好的", "可以"]
        is_confirming = any(kw in text.lower() for kw in confirm_keywords)
        
        # Update intent with simple extraction
        updated_intent = current_intent.copy()
        if not updated_intent.get("topic"):
            updated_intent["topic"] = text[:100]
        
        updated_intent["original_input"] = f"{current_intent.get('original_input', '')} {text}".strip()
        
        if is_confirming and updated_intent.get("topic"):
            return {
                "success": True,
                "needs_clarification": False,
                "questions": [],
                "updated_intent": updated_intent,
                "ready_to_generate": True,
                "ai_response": "Great! Starting video generation..."
            }
        
        # Ask for style if topic exists but style doesn't
        if updated_intent.get("topic") and not updated_intent.get("style"):
            return {
                "success": True,
                "needs_clarification": True,
                "questions": ["What visual style would you prefer? (cinematic, cartoon, realistic, etc.)"],
                "updated_intent": updated_intent,
                "ready_to_generate": False,
                "ai_response": f"Got it! You want a video about '{updated_intent['topic'][:50]}'. What visual style would you prefer?"
            }
        
        return {
            "success": True,
            "needs_clarification": False,
            "questions": [],
            "updated_intent": updated_intent,
            "ready_to_generate": True,
            "ai_response": "I understand! Let me create that video for you."
        }


# Singleton instance
clarification_agent = ClarificationAgent()

