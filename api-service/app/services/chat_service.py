import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from ..repositories.chat_repository import ChatRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.settings_repository import ChatSettingsRepository
from ..database.models import ChatSession, Message, ChatSettings as ChatSettingsModel
from ..schemas.chat_schemas import ChatSessionCreate, ChatSessionUpdate, CreateChatRequest
from ..schemas.message_schemas import SendMessageRequest
from ..schemas.settings_schemas import ChatSettingsUpdate, ChatSettings
from .ai_client import get_ai_client, AIServiceError

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations"""
    
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.message_repo = MessageRepository()
        self.settings_repo = ChatSettingsRepository()
        self.ai_client = get_ai_client()
    
    def get_user_chats(
        self,
        db: Session,
        user_id: UUID,
        page: int = 1,
        per_page: int = 50,
        include_archived: bool = False
    ) -> List[ChatSession]:
        """Get user's chats with pagination"""
        skip = (page - 1) * per_page
        return self.chat_repo.get_user_chats(
            db, user_id, skip=skip, limit=per_page, include_archived=include_archived
        )
    
    def get_chat_with_messages(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        message_limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get chat with messages and settings, ensuring session ownership"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return None
        
        # Get chat with messages
        chat_with_messages = self.chat_repo.get_chat_with_messages(db, chat_id, message_limit)
        if not chat_with_messages:
            return None
        
        # Get chat settings
        settings = self.settings_repo.get_or_create_by_chat_id(db, chat.id)
        chat_settings_dict = None
        if settings:
            chat_settings = ChatSettings.from_orm(settings)
            chat_settings_dict = chat_settings.dict()
        
        # Convert to dict and add settings
        result = {
            **chat_with_messages.__dict__,
            'settings': chat_settings_dict
        }
        
        return result
    
    async def create_chat(
        self,
        db: Session,
        session_id: str,
        request: CreateChatRequest
    ) -> ChatSession:
        """Create a new chat session"""
        # Generate title if not provided
        title = request.title or "New Chat"
        
        # Create chat session
        chat_data = ChatSessionCreate(
            title=title,
            model_name=request.model_name,
            session_id=session_id
        )
        
        chat = self.chat_repo.create(db, obj_in=chat_data)
        
        # If initial message provided, send it
        if request.initial_message:
            try:
                await self.send_message_to_chat(
                    db, chat.id, session_id, 
                    SendMessageRequest(content=request.initial_message)
                )
                
                # Generate better title from first message
                title = self._generate_title_from_message(request.initial_message)
                if title != request.initial_message:
                    update_data = ChatSessionUpdate(title=title)
                    chat = self.chat_repo.update(db, db_obj=chat, obj_in=update_data)
                    
            except Exception as e:
                logger.error(f"Failed to send initial message: {e}")
        
        return chat
    
    def update_chat(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        update_data: ChatSessionUpdate
    ) -> Optional[ChatSession]:
        """Update chat session"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return None
        
        return self.chat_repo.update(db, db_obj=chat, obj_in=update_data)
    
    def delete_chat(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str
    ) -> bool:
        """Delete chat session"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return False
        
        deleted = self.chat_repo.delete(db, id=chat_id)
        return deleted is not None
    
    def archive_chat(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        archived: bool = True
    ) -> Optional[ChatSession]:
        """Archive or unarchive chat"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return None
        
        return self.chat_repo.archive_chat(db, chat_id, archived)
    
    def pin_chat(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        pinned: bool = True
    ) -> Optional[ChatSession]:
        """Pin or unpin chat"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return None
        
        return self.chat_repo.pin_chat(db, chat_id, pinned)
    
    async def send_message(
        self,
        db: Session,
        chat_id: UUID,
        user_id: UUID,
        request: SendMessageRequest
    ) -> Dict[str, Any]:
        """Send message and get AI response"""
        # Verify chat ownership
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.user_id != user_id:
            raise ValueError("Chat not found or access denied")
        
        try:
            # Add user message
            user_message = self.message_repo.add_message(
                db, chat_id, "user", request.content
            )
            
            # Get conversation context
            context_messages = self.message_repo.get_conversation_context(
                db, chat_id, max_messages=10
            )
            
            # Prepare messages for AI service
            ai_messages = []
            for msg in context_messages:
                ai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Get AI response
            try:
                ai_response = await self.ai_client.generate_response(
                    model_id=chat.model_name,
                    messages=ai_messages,
                    parameters=request.model_parameters
                )
                
                # Add assistant message
                assistant_message = self.message_repo.add_message(
                    db, chat_id, "assistant", ai_response
                )
                
                # Update chat's last message time
                self.chat_repo.update_last_message_time(db, chat_id)
                
                return {
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "chat_id": chat_id
                }
                
            except AIServiceError as e:
                logger.error(f"AI service error: {e}")
                # Add error message
                error_message = self.message_repo.add_message(
                    db, chat_id, "assistant", 
                    "I'm sorry, I'm experiencing technical difficulties. Please try again.",
                    message_metadata={"error": str(e)}
                )
                
                return {
                    "user_message": user_message,
                    "assistant_message": error_message,
                    "chat_id": chat_id,
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            raise e
    
    def search_chats(
        self,
        db: Session,
        session_id: str,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> List[ChatSession]:
        """Search session's chats"""
        skip = (page - 1) * per_page
        return self.chat_repo.search_session_chats(db, session_id, query, skip=skip, limit=per_page)
    
    def get_chat_statistics(
        self,
        db: Session,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get chat statistics for user"""
        total_chats = self.chat_repo.get_user_chat_count(db, user_id, include_archived=True)
        active_chats = self.chat_repo.get_user_chat_count(db, user_id, include_archived=False)
        pinned_chats = len(self.chat_repo.get_pinned_chats(db, user_id))
        
        return {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "archived_chats": total_chats - active_chats,
            "pinned_chats": pinned_chats
        }
    
    def _generate_title_from_message(self, message: str, max_length: int = 50) -> str:
        """Generate chat title from first message"""
        # Simple title generation - take first sentence or truncate
        sentences = message.split('.')
        title = sentences[0].strip()
        
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."
        
        return title or "New Chat"
    
    # Session-based methods (new session-based API)
    
    def get_session_chats(
        self,
        db: Session,
        session_id: str,
        page: int = 1,
        per_page: int = 50,
        include_archived: bool = False,
        filter_archived_only: bool = False,
        filter_pinned_only: bool = False
    ) -> List[ChatSession]:
        """Get session's chats with pagination and filtering"""
        skip = (page - 1) * per_page
        return self.chat_repo.get_session_chats(
            db, session_id, skip=skip, limit=per_page, 
            include_archived=include_archived,
            filter_archived_only=filter_archived_only,
            filter_pinned_only=filter_pinned_only
        )
    
    async def send_message_to_session(
        self,
        db: Session,
        session_id: str,
        request: SendMessageRequest
    ) -> Dict[str, Any]:
        """Send message to session, creating chat if needed"""
        # Get or create an active chat for this session
        chat = self.chat_repo.get_or_create_session_chat(db, session_id)
        
        # Use the internal method which now includes settings integration
        return await self._send_message_to_chat_internal(db, chat.id, request)
    
    async def send_message_to_chat(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        request: SendMessageRequest
    ) -> Dict[str, Any]:
        """Send message to specific chat (session-based)"""
        # Verify chat belongs to session
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            raise ValueError("Chat not found or access denied")
        
        return await self._send_message_to_chat_internal(db, chat_id, request)
    
    async def _send_message_to_chat_internal(
        self,
        db: Session,
        chat_id: UUID,
        request: SendMessageRequest
    ) -> Dict[str, Any]:
        """Internal method to send message to a chat"""
        chat = self.chat_repo.get(db, chat_id)
        if not chat:
            raise ValueError("Chat not found")
        
        try:
            # Add user message
            user_message = self.message_repo.add_message(
                db, chat_id, "user", request.content
            )
            
            # Get conversation context
            context_messages = self.message_repo.get_conversation_context(
                db, chat_id, max_messages=10
            )
            
            # Get chat settings to apply to AI generation
            # Use the chat's UUID id for settings lookup
            chat_settings = self.settings_repo.get_or_create_by_chat_id(db, chat.id)
            
            # Debug logging for system prompt
            logger.info(f"[CHAT_MESSAGE] Settings loaded - system_prompt: '{chat_settings.system_prompt}' (type: {type(chat_settings.system_prompt)})")
            
            # Prepare messages for AI service, including system prompt
            ai_messages = []
            
            # Add system prompt if configured
            if chat_settings.system_prompt and chat_settings.system_prompt.strip():
                logger.info(f"[CHAT_MESSAGE] Adding system prompt: '{chat_settings.system_prompt}'")
                ai_messages.append({
                    "role": "system",
                    "content": chat_settings.system_prompt
                })
            else:
                logger.info(f"[CHAT_MESSAGE] System prompt not added - empty or null: '{chat_settings.system_prompt}'")
            
            for msg in context_messages:
                ai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare parameters using chat settings
            ai_parameters = {
                "temperature": float(chat_settings.temperature) if chat_settings.temperature else 0.7,
                "max_length": chat_settings.max_tokens if chat_settings.max_tokens else 1000,
            }
            
            # Override with any request-specific parameters
            if request.model_parameters:
                ai_parameters.update(request.model_parameters)
            
            logger.info(f"[CHAT_MESSAGE] Sending to AI with settings - Chat ID: {chat_id}, Parameters: {ai_parameters}")
            
            # Get AI response
            try:
                ai_response = await self.ai_client.generate_response(
                    model_id=chat.model_name,
                    messages=ai_messages,
                    parameters=ai_parameters
                )
                
                # Add assistant message
                assistant_message = self.message_repo.add_message(
                    db, chat_id, "assistant", ai_response
                )
                
                # Update chat's last message time and message count
                updated_chat = self.chat_repo.update_last_message_time(db, chat_id)
                
                return {
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "chat_id": chat_id,
                    "message_count": updated_chat.message_count if updated_chat else chat.message_count
                }
                
            except AIServiceError as e:
                logger.error(f"AI service error: {e}")
                # Add error message
                error_message = self.message_repo.add_message(
                    db, chat_id, "assistant", 
                    "I'm sorry, I'm experiencing technical difficulties. Please try again.",
                    message_metadata={"error": str(e)}
                )
                
                # Update chat's last message time and message count for error case too
                updated_chat = self.chat_repo.update_last_message_time(db, chat_id)
                
                return {
                    "user_message": user_message,
                    "assistant_message": error_message,
                    "chat_id": chat_id,
                    "error": str(e),
                    "message_count": updated_chat.message_count if updated_chat else chat.message_count
                }
                
        except Exception as e:
            logger.error(f"Error in _send_message_to_chat_internal: {e}")
            raise e
    
    def add_system_message(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        content: str
    ) -> Message:
        """Add system message to specific chat"""
        # Verify chat belongs to session
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            raise ValueError("Chat not found or access denied")
        
        try:
            # Add system message
            system_message = self.message_repo.add_message(
                db, chat_id, "system", content
            )
            
            # Update chat's last message time (but don't increment count for system messages)
            self.chat_repo.update_last_message_time(db, chat_id, update_count=False)
            
            return system_message
            
        except Exception as e:
            logger.error(f"Error adding system message: {e}")
            raise e
    
    def get_chat_settings(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str
    ) -> Optional[ChatSettings]:
        """Get chat settings for a specific chat"""
        # Verify chat belongs to session
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            return None
        
        # Get or create settings for this chat
        # Use the chat's UUID id for settings lookup
        settings = self.settings_repo.get_or_create_by_chat_id(db, chat.id)
        return ChatSettings.from_orm(settings)
    
    def update_chat_settings(
        self,
        db: Session,
        chat_id: UUID,
        session_id: str,
        settings_update: ChatSettingsUpdate
    ) -> Optional[ChatSettings]:
        """Update chat settings for a specific chat"""
        logger.info(f"[CHAT_SETTINGS] Update request - Chat ID: {chat_id}, Session: {session_id}")
        
        # Verify chat belongs to session
        chat = self.chat_repo.get(db, chat_id)
        if not chat or chat.session_id != session_id:
            logger.warning(f"[CHAT_SETTINGS] Access denied - Chat ID: {chat_id}, Session: {session_id}")
            return None
        
        # Get or create settings
        # Use the chat's UUID id for settings lookup
        settings = self.settings_repo.get_or_create_by_chat_id(db, chat.id)
        old_settings = {
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "system_prompt": settings.system_prompt
        } if settings else {}
        
        logger.info(f"[CHAT_SETTINGS] Previous settings - Chat ID: {chat_id}: {old_settings}")
        
        # Log the requested updates
        new_settings = settings_update.dict(exclude_unset=True)
        logger.info(f"[CHAT_SETTINGS] New settings requested - Chat ID: {chat_id}: {new_settings}")
        
        # Update settings
        updated_settings = self.settings_repo.update(db, db_obj=settings, obj_in=settings_update)
        
        if updated_settings:
            final_settings = {
                "temperature": updated_settings.temperature,
                "max_tokens": updated_settings.max_tokens,
                "system_prompt": updated_settings.system_prompt
            }
            logger.info(f"[CHAT_SETTINGS] Settings updated successfully - Chat ID: {chat_id}: {final_settings}")
            return ChatSettings.from_orm(updated_settings)
        else:
            logger.error(f"[CHAT_SETTINGS] Failed to update settings - Chat ID: {chat_id}")
            return None
