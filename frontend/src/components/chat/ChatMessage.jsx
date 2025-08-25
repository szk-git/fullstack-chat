import React, { memo } from 'react';
import './ChatMessage.css';

const ChatMessage = memo(({ 
  message, 
  sender, 
  timestamp, 
  isError = false, 
  isLoading = false,
  isPending = false 
}) => {
  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return '';
    }
  };

  const isUser = sender === 'user';
  const isAssistant = sender === 'assistant' || sender === 'bot';
  const isSystem = sender === 'system';

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="typing-indicator" aria-label="AI is typing">
          <span></span>
          <span></span>
          <span></span>
        </div>
      );
    }

    // Handle different message types safely
    let content = '';
    if (typeof message === 'string') {
      content = message;
    } else if (typeof message === 'object' && message !== null) {
      content = JSON.stringify(message, null, 2);
    } else {
      content = message?.toString() || '';
    }

    // Debug logging for system messages
    if (isSystem) {
      console.log('System message debug:', { message, content, sender });
    }

    // Show fallback only if content is truly empty or undefined
    if (!content || content.trim() === '') {
      console.warn('Empty message content detected:', { message, sender, timestamp });
      return (
        <div className="message-content">
          {isSystem ? 'System notification' : 'Empty message'}
        </div>
      );
    }

    return (
      <div className="message-content">
        {content}
      </div>
    );
  };

  return (
    <div 
      className={`chat-message ${isUser ? 'user' : isSystem ? 'system' : 'assistant'} ${isError ? 'error' : ''} ${isLoading ? 'loading' : ''} ${isPending ? 'pending' : ''}`}
      role="group"
      aria-label={`${isUser ? 'Your' : isSystem ? 'System' : 'Assistant'} message ${isError ? 'with error' : ''} ${isPending ? '(sending...)' : ''}`}
    >
      <div className="message-bubble">
        {renderContent()}
        {!isLoading && timestamp && (
          <time 
            className="message-timestamp" 
            dateTime={timestamp}
            title={new Date(timestamp).toLocaleString()}
          >
            {formatTime(timestamp)}
            {isPending && (
              <span className="pending-indicator" title="Sending...">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12,6 12,12 16,14"/>
                </svg>
              </span>
            )}
          </time>
        )}
      </div>
    </div>
  );
});

ChatMessage.displayName = 'ChatMessage';

export default ChatMessage;
