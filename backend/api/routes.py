"""
REST API Routes - Simple and direct
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path

from models.schemas import (
    VideoRequest, 
    TaskResponse, 
    TaskStatusResponse,
    TaskStatus,
    TaskPhase,
    ConversationRequest,
    ConversationResponse
)
from services.task_manager import task_manager
from services.conversation_manager import conversation_manager, ConversationState
from agents import orchestrator, clarification_agent, speech_agent

router = APIRouter()

# Video files directory
VIDEO_DIR = Path("generated/videos")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "KIWI-Video API"}


@router.post("/video/create", response_model=TaskResponse)
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Create a new video generation task.
    Returns immediately with task_id, processing happens in background.
    """
    # Validate input
    if not request.audio_data and not request.text_input:
        raise HTTPException(
            status_code=400, 
            detail="Either audio_data or text_input is required"
        )
    
    # Create task
    task = task_manager.create_task({
        "audio_data": request.audio_data,
        "text_input": request.text_input
    })
    
    # Define the processor function
    async def process_video(on_status_update):
        orchestrator.set_status_handler(on_status_update)
        return await orchestrator.process_video_request(
            task_id=task.id,
            audio_data=request.audio_data,
            text_input=request.text_input
        )
    
    # Start processing in background
    task_manager.start_task_async(task.id, process_video)
    
    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message="Video generation task created. Use WebSocket or polling to track progress."
    )


@router.get("/video/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a video generation task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        phase=task.phase,
        progress=task.progress,
        message=task.message,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/video/tasks", response_model=List[dict])
async def list_tasks():
    """List all tasks (for debugging)"""
    return task_manager.get_all_tasks()


@router.delete("/video/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task (for cleanup)"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_manager.tasks[task_id]
    
    return {"message": f"Task {task_id} deleted"}


@router.get("/video/file/{filename}")
async def get_video_file(filename: str):
    """Serve generated video files"""
    # Security: only allow mp4 files, prevent directory traversal
    if not filename.endswith(".mp4") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    video_path = VIDEO_DIR / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename
    )


# ============== Conversation Endpoints ==============

@router.post("/conversation/message", response_model=ConversationResponse)
async def send_message(request: ConversationRequest, background_tasks: BackgroundTasks):
    """
    Send a message in a conversation.
    Supports multi-turn dialog with clarification.
    """
    # Get or create conversation
    conversation = conversation_manager.get_or_create(request.conversation_id)
    
    # Get user input
    user_text = request.message
    
    # If audio, transcribe first
    if request.audio_data and not user_text:
        result = await speech_agent.run({"audio_data": request.audio_data})
        if result.get("success"):
            user_text = result.get("transcription", "")
        else:
            return ConversationResponse(
                conversation_id=conversation.id,
                state=conversation.state.value,
                ai_response="Sorry, I couldn't understand the audio. Please try again or type your message.",
                needs_clarification=True,
                questions=["Could you please repeat that or type your message?"],
                accumulated_intent=conversation.accumulated_intent,
                ready_to_generate=False,
                messages=conversation.get_history()
            )
    
    if not user_text:
        raise HTTPException(status_code=400, detail="No message or audio provided")
    
    # Add user message to history
    conversation.add_message("user", user_text)
    
    # If user explicitly confirms, start generation
    if request.confirm_generate and conversation.accumulated_intent.get("topic"):
        conversation.state = ConversationState.CONFIRMED
        
        # Create video task
        task = task_manager.create_task({
            "text_input": conversation.accumulated_intent.get("original_input", user_text),
            "intent": conversation.accumulated_intent
        })
        conversation.task_id = task.id
        conversation.state = ConversationState.GENERATING
        
        # Start video generation
        async def process_video(on_status_update):
            orchestrator.set_status_handler(on_status_update)
            return await orchestrator.process_video_request(
                task_id=task.id,
                text_input=conversation.accumulated_intent.get("original_input", user_text)
            )
        
        task_manager.start_task_async(task.id, process_video)
        
        ai_response = "Great! I'm starting to generate your video now. This may take 1-2 minutes..."
        conversation.add_message("assistant", ai_response)
        
        return ConversationResponse(
            conversation_id=conversation.id,
            state=conversation.state.value,
            ai_response=ai_response,
            needs_clarification=False,
            questions=[],
            accumulated_intent=conversation.accumulated_intent,
            ready_to_generate=False,
            task_id=task.id,
            messages=conversation.get_history()
        )
    
    # Use ClarificationAgent to analyze
    result = await clarification_agent.run({
        "text": user_text,
        "conversation_history": conversation.get_history(),
        "current_intent": conversation.accumulated_intent
    })
    
    if not result.get("success"):
        ai_response = "I'm having trouble understanding. Could you please rephrase?"
        conversation.add_message("assistant", ai_response)
        return ConversationResponse(
            conversation_id=conversation.id,
            state=conversation.state.value,
            ai_response=ai_response,
            needs_clarification=True,
            questions=["Could you tell me more about what kind of video you want?"],
            accumulated_intent=conversation.accumulated_intent,
            ready_to_generate=False,
            messages=conversation.get_history()
        )
    
    # Update intent
    updated_intent = result.get("updated_intent", {})
    conversation.update_intent(updated_intent)
    
    # Get AI response
    ai_response = result.get("ai_response", "")
    needs_clarification = result.get("needs_clarification", False)
    questions = result.get("questions", [])
    ready_to_generate = result.get("ready_to_generate", False)
    
    # Update state
    if ready_to_generate:
        conversation.state = ConversationState.CONFIRMED
    elif needs_clarification:
        conversation.state = ConversationState.CLARIFYING
    
    # Add AI response to history
    if ai_response:
        conversation.add_message("assistant", ai_response)
    
    return ConversationResponse(
        conversation_id=conversation.id,
        state=conversation.state.value,
        ai_response=ai_response,
        needs_clarification=needs_clarification,
        questions=questions,
        accumulated_intent=conversation.accumulated_intent,
        ready_to_generate=ready_to_generate,
        messages=conversation.get_history()
    )


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation.to_dict()


@router.post("/conversation/{conversation_id}/generate")
async def start_generation(conversation_id: str, background_tasks: BackgroundTasks):
    """Start video generation for a confirmed conversation"""
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if not conversation.accumulated_intent.get("topic"):
        raise HTTPException(status_code=400, detail="No video intent defined yet")
    
    # Create task
    task = task_manager.create_task({
        "text_input": conversation.accumulated_intent.get("original_input", ""),
        "intent": conversation.accumulated_intent
    })
    conversation.task_id = task.id
    conversation.state = ConversationState.GENERATING
    
    # Start processing
    async def process_video(on_status_update):
        orchestrator.set_status_handler(on_status_update)
        return await orchestrator.process_video_request(
            task_id=task.id,
            text_input=conversation.accumulated_intent.get("original_input", "")
        )
    
    task_manager.start_task_async(task.id, process_video)
    
    return {
        "conversation_id": conversation.id,
        "task_id": task.id,
        "message": "Video generation started"
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation_manager.delete_conversation(conversation_id)
    return {"message": f"Conversation {conversation_id} deleted"}

