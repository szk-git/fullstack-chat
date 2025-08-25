from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from uuid import UUID

from .base_repository import BaseRepository
from ..database.models import Message
from ..schemas.message_schemas import MessageCreate, MessageUpdate


class MessageRepository(BaseRepository[Message, MessageCreate, MessageUpdate]):
    """Repository for message operations"""
    
    def __init__(self):
        super().__init__(Message)
    
    def get_chat_messages(
        self,
        db: Session,
        session_id: UUID,
        skip: int = 0,
        limit: int = 50,
        order_desc: bool = False
    ) -> List[Message]:
        """Get messages for a chat session"""
        query = db.query(self.model).filter(self.model.session_id == session_id)
        
        if order_desc:
            query = query.order_by(desc(self.model.created_at))
        else:
            query = query.order_by(self.model.created_at)
        
        return query.offset(skip).limit(limit).all()
    
    def get_recent_messages(
        self,
        db: Session,
        session_id: UUID,
        count: int = 10
    ) -> List[Message]:
        """Get most recent messages for context"""
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.created_at))
            .limit(count)
            .all()
        )
    
    def get_conversation_context(
        self,
        db: Session,
        session_id: UUID,
        max_messages: int = 20
    ) -> List[Message]:
        """Get conversation context in chronological order"""
        messages = (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.created_at))
            .limit(max_messages)
            .all()
        )
        # Return in chronological order (oldest first)
        return list(reversed(messages))
    
    def add_message(
        self,
        db: Session,
        session_id: UUID,
        role: str,
        content: str,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a new message to a chat session"""
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "message_metadata": message_metadata or {}
        }
        return self.create(db, obj_in=message_data)
    
    def get_message_count(self, db: Session, session_id: UUID) -> int:
        """Get total message count for a chat session"""
        return db.query(self.model).filter(self.model.session_id == session_id).count()
    
    def get_user_messages(self, db: Session, session_id: UUID) -> List[Message]:
        """Get only user messages from a chat session"""
        return (
            db.query(self.model)
            .filter(and_(self.model.session_id == session_id, self.model.role == "user"))
            .order_by(self.model.created_at)
            .all()
        )
    
    def get_assistant_messages(self, db: Session, session_id: UUID) -> List[Message]:
        """Get only assistant messages from a chat session"""
        return (
            db.query(self.model)
            .filter(and_(self.model.session_id == session_id, self.model.role == "assistant"))
            .order_by(self.model.created_at)
            .all()
        )
    
    def search_messages(
        self,
        db: Session,
        session_id: UUID,
        search_query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Message]:
        """Search messages by content"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.session_id == session_id,
                    self.model.content.ilike(f"%{search_query}%")
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def delete_session_messages(self, db: Session, session_id: UUID) -> int:
        """Delete all messages for a chat session"""
        deleted_count = (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .delete()
        )
        db.commit()
        return deleted_count
    
    def get_last_message(self, db: Session, session_id: UUID) -> Optional[Message]:
        """Get the last message in a chat session"""
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.created_at))
            .first()
        )
    
    def get_first_user_message(self, db: Session, session_id: UUID) -> Optional[Message]:
        """Get the first user message for title generation"""
        return (
            db.query(self.model)
            .filter(and_(self.model.session_id == session_id, self.model.role == "user"))
            .order_by(self.model.created_at)
            .first()
        )
