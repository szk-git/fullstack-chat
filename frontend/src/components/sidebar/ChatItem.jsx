import React, { memo } from 'react';
import './ChatItem.css';

const ChatItem = memo(({ chat, isActive, onSelect, onUpdateChat }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'Just now';
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Just now';
    }
    
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const handleClick = () => {
    if (onSelect) {
      onSelect();
    }
  };

  return (
    <div 
      className={`chat-item ${isActive ? 'active' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Chat: ${chat.title}`}
    >
      <div className="chat-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3.04 1.05 4.35L2 22l5.65-1.05C9.96 21.64 11.46 22 13 22h7c1.1 0 2-.9 2-2V12c0-5.52-4.48-10-10-10z"/>
        </svg>
      </div>
      
      <div className="chat-content">
        <div className="chat-header">
          <div className="chat-title-wrapper">
            <h3 className="chat-title">{chat.title}</h3>
            <div className="chat-indicators">
              {(chat.pinned || chat.is_pinned) && (
                <span className="chat-indicator pinned" title="Pinned">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3 10h7l-6 5 2 10-6-8-6 8 2-10-6-5h7z"/>
                  </svg>
                </span>
              )}
              {(chat.archived || chat.is_archived) && (
                <span className="chat-indicator archived" title="Archived">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polyline points="21,8 21,21 3,21 3,8"/>
                    <rect x="1" y="3" width="22" height="5"/>
                    <line x1="10" y1="12" x2="14" y2="12"/>
                  </svg>
                </span>
              )}
            </div>
          </div>
          <span className="chat-time">{formatDate(chat.updated_at || chat.created_at)}</span>
        </div>
      </div>
    </div>
  );
});

ChatItem.displayName = 'ChatItem';

export default ChatItem;
