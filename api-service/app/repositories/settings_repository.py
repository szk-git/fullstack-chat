from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

from .base_repository import BaseRepository
from ..database.models import ChatSettings
from ..schemas.settings_schemas import ChatSettingsCreate, ChatSettingsUpdate


class ChatSettingsRepository(BaseRepository[ChatSettings, ChatSettingsCreate, ChatSettingsUpdate]):
    """Repository for chat settings operations"""
    
    def __init__(self):
        super().__init__(ChatSettings)
    
    def get_by_session_id(self, db: Session, session_id: UUID) -> Optional[ChatSettings]:
        """Get chat settings by session ID"""
        return db.query(self.model).filter(self.model.session_id == session_id).first()
    
    def get_or_create_by_session_id(self, db: Session, session_id: UUID) -> ChatSettings:
        """Get or create chat settings for a session"""
        settings = self.get_by_session_id(db, session_id)
        if not settings:
            # Create default settings
            settings_data = {
                "session_id": session_id,
                "temperature": "0.7",
                "max_tokens": 1000,
                "system_prompt": None
            }
            settings = self.model(**settings_data)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    
    def update_by_session_id(
        self, 
        db: Session, 
        session_id: UUID, 
        obj_in: ChatSettingsUpdate
    ) -> Optional[ChatSettings]:
        """Update chat settings by session ID"""
        settings = self.get_by_session_id(db, session_id)
        if settings:
            return self.update(db, db_obj=settings, obj_in=obj_in)
        return None
    
    def delete_by_session_id(self, db: Session, session_id: UUID) -> bool:
        """Delete chat settings by session ID"""
        settings = self.get_by_session_id(db, session_id)
        if settings:
            db.delete(settings)
            db.commit()
            return True
        return False
    
    def get_by_chat_id(self, db: Session, chat_id: UUID) -> Optional[ChatSettings]:
        """Get chat settings by chat ID (alias for get_by_session_id for clarity)"""
        return self.get_by_session_id(db, chat_id)
    
    def get_or_create_by_chat_id(self, db: Session, chat_id: UUID) -> ChatSettings:
        """Get or create chat settings for a chat (alias for get_or_create_by_session_id for clarity)"""
        return self.get_or_create_by_session_id(db, chat_id)
