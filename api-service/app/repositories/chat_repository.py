from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from uuid import UUID

from .base_repository import BaseRepository
from ..database.models import ChatSession, Message
from ..schemas.chat_schemas import ChatSessionCreate, ChatSessionUpdate


class ChatRepository(BaseRepository[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    """Repository for chat session operations"""
    
    def __init__(self):
        super().__init__(ChatSession)
    
    def get_user_chats(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False
    ) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        query = db.query(self.model).filter(self.model.user_id == user_id)
        
        if not include_archived:
            query = query.filter(self.model.is_archived == False)
        
        return (
            query.order_by(desc(self.model.last_message_at), desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_pinned_chats(self, db: Session, user_id: UUID) -> List[ChatSession]:
        """Get pinned chats for a user"""
        return (
            db.query(self.model)
            .filter(and_(self.model.user_id == user_id, self.model.is_pinned == True))
            .order_by(desc(self.model.last_message_at))
            .all()
        )
    
    def search_chats(
        self,
        db: Session,
        user_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[ChatSession]:
        """Search chats by title or content"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.title.ilike(f"%{query}%")
                )
            )
            .order_by(desc(self.model.last_message_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def archive_chat(self, db: Session, chat_id: UUID, archived: bool = True) -> Optional[ChatSession]:
        """Archive or unarchive a chat"""
        chat = self.get(db, chat_id)
        if chat:
            chat.is_archived = archived
            db.commit()
            db.refresh(chat)
        return chat
    
    def pin_chat(self, db: Session, chat_id: UUID, pinned: bool = True) -> Optional[ChatSession]:
        """Pin or unpin a chat"""
        chat = self.get(db, chat_id)
        if chat:
            chat.is_pinned = pinned
            db.commit()
            db.refresh(chat)
        return chat
    
    def update_last_message_time(self, db: Session, chat_id: UUID, update_count: bool = True) -> Optional[ChatSession]:
        """Update the last message timestamp and optionally sync message count"""
        from sqlalchemy import func
        chat = self.get(db, chat_id)
        if chat:
            chat.last_message_at = func.now()
            # Sync the message count only if requested (not for system messages)
            if update_count:
                self._sync_message_count(db, chat)
            db.commit()
            db.refresh(chat)
        return chat
    
    def sync_message_count(self, db: Session, chat_id: UUID) -> Optional[ChatSession]:
        """Synchronize the message count for a chat session"""
        chat = self.get(db, chat_id)
        if chat:
            self._sync_message_count(db, chat)
            db.commit()
            db.refresh(chat)
        return chat
    
    def _sync_message_count(self, db: Session, chat: ChatSession) -> None:
        """Internal method to sync message count with actual message count"""
        # Count actual messages for this chat session
        actual_count = (
            db.query(Message)
            .filter(Message.session_id == chat.id)
            .count()
        )
        chat.message_count = actual_count
    
    def get_chat_with_messages(
        self,
        db: Session,
        chat_id: UUID,
        message_limit: int = 50
    ) -> Optional[ChatSession]:
        """Get chat with recent messages"""
        chat = (
            db.query(self.model)
            .filter(self.model.id == chat_id)
            .first()
        )
        
        if chat:
            # Load recent messages
            recent_messages = (
                db.query(Message)
                .filter(Message.session_id == chat_id)
                .order_by(desc(Message.created_at))
                .limit(message_limit)
                .all()
            )
            # Reverse to get chronological order
            chat.messages = list(reversed(recent_messages))
        
        return chat
    
    def get_user_chat_count(self, db: Session, user_id: UUID, include_archived: bool = False) -> int:
        """Get total chat count for a user"""
        query = db.query(self.model).filter(self.model.user_id == user_id)
        
        if not include_archived:
            query = query.filter(self.model.is_archived == False)
        
        return query.count()
    
    def delete_user_chats(self, db: Session, user_id: UUID) -> int:
        """Delete all chats for a user (cascade will handle messages)"""
        deleted_count = (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .delete()
        )
        db.commit()
        return deleted_count
    
    # Session-based methods (new session-based API)
    
    def get_session_chats(
        self,
        db: Session,
        session_id: str,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False,
        filter_archived_only: bool = False,
        filter_pinned_only: bool = False
    ) -> List[ChatSession]:
        """Get all chat sessions for a session ID with filtering"""
        query = db.query(self.model).filter(self.model.session_id == session_id)
        
        if filter_archived_only:
            # Show only archived chats
            query = query.filter(self.model.is_archived == True)
        elif filter_pinned_only:
            # Show only pinned chats (exclude archived unless explicitly included)
            query = query.filter(self.model.is_pinned == True)
            if not include_archived:
                query = query.filter(self.model.is_archived == False)
        elif not include_archived:
            # Default: exclude archived chats
            query = query.filter(self.model.is_archived == False)
        
        return (
            query.order_by(desc(self.model.last_message_at), desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_or_create_session_chat(self, db: Session, session_id: str) -> ChatSession:
        """Get or create an active chat for a session"""
        # Try to get the most recent non-archived chat for this session
        existing_chat = (
            db.query(self.model)
            .filter(
                and_(
                    self.model.session_id == session_id,
                    self.model.is_archived == False
                )
            )
            .order_by(desc(self.model.last_message_at), desc(self.model.created_at))
            .first()
        )
        
        if existing_chat:
            return existing_chat
        
        # Create new chat if none exists
        from ..schemas.chat_schemas import ChatSessionCreate
        new_chat_data = ChatSessionCreate(
            session_id=session_id,
            title="New Chat",
            model_name="facebook/blenderbot-400M-distill"  # Default model
        )
        
        return self.create(db, obj_in=new_chat_data)
    
    def search_session_chats(
        self,
        db: Session,
        session_id: str,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[ChatSession]:
        """Search chats by title or content for a session"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.session_id == session_id,
                    self.model.title.ilike(f"%{query}%")
                )
            )
            .order_by(desc(self.model.last_message_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
