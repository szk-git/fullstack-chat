from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...core.database import get_db
from ...services.chat_service import ChatService
from ...schemas.chat_schemas import (
    ChatSession, ChatSessionWithMessages, ChatListResponse,
    CreateChatRequest, CreateChatResponse, ChatSessionUpdate
)
from ...schemas.message_schemas import SendMessageRequest, SendMessageResponse, Message, SystemMessageResponse
from ...schemas.settings_schemas import ChatSettings, ChatSettingsUpdate, ChatSettingsResponse

router = APIRouter()
chat_service = ChatService()


async def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Get session ID from header or generate a default one"""
    import uuid
    if x_session_id:
        return x_session_id
    # Generate a default session ID if none provided
    return f"session_{uuid.uuid4().hex[:16]}"


@router.get("/", response_model=ChatListResponse)
async def list_chats(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Include archived chats"),
    filter: Optional[str] = Query(None, description="Filter chats by status: 'active', 'pinned', 'archived'"),
    search: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """List session's chat conversations"""
    try:
        if search:
            chats = chat_service.search_chats(db, session_id, search, page, per_page)
            total = len(chats)  # Simplified count for search
        else:
            # Handle filter parameter
            if filter == 'archived':
                chats = chat_service.get_session_chats(db, session_id, page, per_page, include_archived=True, filter_archived_only=True)
            elif filter == 'pinned':
                chats = chat_service.get_session_chats(db, session_id, page, per_page, include_archived=False, filter_pinned_only=True)
            elif filter == 'active':
                chats = chat_service.get_session_chats(db, session_id, page, per_page, include_archived=False)
            else:
                # Default to active chats (backward compatibility)
                chats = chat_service.get_session_chats(db, session_id, page, per_page, include_archived or False)
            total = len(chats)  # This should be from a count query in production
        
        # Enhanced chats already include message_count from the model
        enhanced_chats = []
        for chat in chats:
            chat_dict = {
                **chat.__dict__,
                "message_count": chat.message_count,
            }
            enhanced_chats.append(chat_dict)
        
        return ChatListResponse(
            chats=enhanced_chats,
            total=total,
            page=page,
            per_page=per_page,
            has_more=len(chats) == per_page
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chats: {str(e)}")


@router.post("/", response_model=CreateChatResponse)
async def create_chat(
    request: CreateChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Create a new chat session"""
    try:
        chat = await chat_service.create_chat(db, session_id, request)
        
        # If initial message was sent, get the response
        message = None
        if request.initial_message:
            from ...repositories.message_repository import MessageRepository
            message_repo = MessageRepository()
            message = message_repo.get_last_message(db, chat.id)
        
        return CreateChatResponse(chat=chat, message=message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")


@router.get("/{chat_id}", response_model=ChatSessionWithMessages)
async def get_chat(
    chat_id: UUID,
    message_limit: int = Query(50, ge=1, le=200, description="Number of recent messages to include"),
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Get chat session with messages"""
    try:
        chat = chat_service.get_chat_with_messages(db, chat_id, session_id, message_limit)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return chat
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {str(e)}")


@router.put("/{chat_id}", response_model=ChatSession)
async def update_chat(
    chat_id: UUID,
    update_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Update chat session"""
    try:
        chat = chat_service.update_chat(db, chat_id, session_id, update_data)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return chat
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chat: {str(e)}")


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Delete chat session"""
    try:
        success = chat_service.delete_chat(db, chat_id, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"message": "Chat deleted successfully", "chat_id": chat_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")


@router.post("/{chat_id}/archive", response_model=ChatSession)
async def archive_chat(
    chat_id: UUID,
    archived: bool = Query(True, description="Archive (true) or unarchive (false)"),
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Archive or unarchive chat"""
    try:
        chat = chat_service.archive_chat(db, chat_id, session_id, archived)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return chat
        
    except HTTPException:
        raise
    except Exception as e:
        action = "archive" if archived else "unarchive"
        raise HTTPException(status_code=500, detail=f"Failed to {action} chat: {str(e)}")


@router.post("/{chat_id}/pin", response_model=ChatSession)
async def pin_chat(
    chat_id: UUID,
    pinned: bool = Query(True, description="Pin (true) or unpin (false)"),
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Pin or unpin chat"""
    try:
        chat = chat_service.pin_chat(db, chat_id, session_id, pinned)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return chat
        
    except HTTPException:
        raise
    except Exception as e:
        action = "pin" if pinned else "unpin"
        raise HTTPException(status_code=500, detail=f"Failed to {action} chat: {str(e)}")


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Send message and get AI response (creates new chat if none exists)"""
    try:
        result = await chat_service.send_message_to_session(db, session_id, request)
        
        return SendMessageResponse(
            user_message=result["user_message"],
            assistant_message=result["assistant_message"],
            chat_id=result["chat_id"],
            message_count=result["message_count"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message_to_chat(
    chat_id: UUID,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Send message to specific chat and get AI response"""
    try:
        result = await chat_service.send_message_to_chat(db, chat_id, session_id, request)
        
        return SendMessageResponse(
            user_message=result["user_message"],
            assistant_message=result["assistant_message"],
            chat_id=result["chat_id"],
            message_count=result["message_count"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/{chat_id}/system-message", response_model=SystemMessageResponse)
async def add_system_message(
    chat_id: UUID,
    request: dict,  # Simple dict with 'content' field
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Add system message to specific chat"""
    try:
        if 'content' not in request:
            raise HTTPException(status_code=400, detail="Content is required")
        
        result = chat_service.add_system_message(db, chat_id, session_id, request['content'])
        
        # Manually construct the Message from the ORM result to ensure all fields are present
        # Note: Using direct construction instead of from_orm() due to serialization issues
        system_message = Message(
            id=result.id,
            session_id=result.session_id,
            role=result.role,
            content=result.content,
            message_metadata=result.message_metadata or {},
            created_at=result.created_at
        )
        
        return SystemMessageResponse(
            message="System message added successfully",
            system_message=system_message,
            chat_id=str(chat_id)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add system message: {str(e)}")


@router.get("/{chat_id}/settings", response_model=ChatSettings)
async def get_chat_settings(
    chat_id: UUID,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Get chat settings for a specific chat"""
    try:
        settings = chat_service.get_chat_settings(db, chat_id, session_id)
        if not settings:
            raise HTTPException(status_code=404, detail="Chat not found or settings not available")
        
        return settings
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat settings: {str(e)}")


@router.put("/{chat_id}/settings", response_model=ChatSettingsResponse)
async def update_chat_settings(
    chat_id: UUID,
    settings_update: ChatSettingsUpdate,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Update chat settings for a specific chat"""
    try:
        settings = chat_service.update_chat_settings(db, chat_id, session_id, settings_update)
        if not settings:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return ChatSettingsResponse(
            settings=settings,
            message="Chat settings updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chat settings: {str(e)}")
