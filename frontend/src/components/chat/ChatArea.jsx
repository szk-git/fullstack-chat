import React, { useEffect, useRef, useState } from 'react';
import ChatHeader from './ChatHeader';
import ChatMessage from './ChatMessage';
import InputBar from './InputBar';
import ModelStatus from '../common/ModelStatus';
import useChatStore from '../../stores/chatStore';
import './ChatArea.css';

const ChatArea = ({ currentChat, onToggleSidebar, sidebarOpen, isMobile, isLoading: parentLoading, connectionStatus }) => {
  // Use chatStore for database operations
  const { 
    sendMessage, 
    deleteChat, 
    isLoading: storeLoading,
    updateChat,
    getActiveMessages 
  } = useChatStore();
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [previousChatId, setPreviousChatId] = useState(null);
  const [forceRefresh, setForceRefresh] = useState(0); // Used to force re-renders
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isInitialLoad = useRef(true);
  
  // Use combined loading state
  const isLoading = storeLoading || parentLoading;

  // Handle chat switching with preserved scroll position
  useEffect(() => {
    const chatChanged = currentChat?.id !== previousChatId;
    
    if (chatChanged) {
      setPreviousChatId(currentChat?.id);
      
      // Always scroll to bottom when opening any chat (with or without messages)
      setTimeout(() => {
        scrollToBottom(true); // force = true to ensure scroll happens
        setShouldAutoScroll(true); // Enable auto-scroll for new messages
      }, 100);
      
      isInitialLoad.current = false;
    } else if (currentChat?.messages && shouldAutoScroll) {
      // For new messages in the current chat, scroll to bottom
      // Check if the last message is from user and force scroll immediately
      const lastMessage = currentChat.messages[currentChat.messages.length - 1];
      if (lastMessage && lastMessage.role === 'user' && (lastMessage.isPending || !lastMessage.isError)) {
        // User just sent a message - force scroll immediately
        setTimeout(() => {
          scrollToBottom(true);
        }, 10);
      } else {
        // For other messages (like AI responses), scroll if near bottom
        scrollToBottomIfNeeded();
      }
    }
  }, [currentChat?.messages, currentChat?.id]);
  
  // Handle setting auto-scroll when chat changes
  useEffect(() => {
    if (currentChat?.id !== previousChatId) {
      // Only reset auto-scroll if user hasn't manually scrolled up
      if (isNearBottom()) {
        setShouldAutoScroll(true);
      }
    }
  }, [currentChat?.id, previousChatId]);

  // Handle scrolling when messages are loaded asynchronously
  useEffect(() => {
    if (currentChat?.messages && currentChat.messages.length > 0) {
      // Small delay to ensure DOM is updated with new messages
      setTimeout(() => {
        scrollToBottom(true);
      }, 50);
    }
  }, [currentChat?.messages?.length]);

  // Check if user is near bottom of chat with improved accuracy
  const isNearBottom = () => {
    if (!messagesContainerRef.current) return true;
    
    const container = messagesContainerRef.current;
    const threshold = 50; // Reduced threshold for more accurate detection
    const currentScrollTop = container.scrollTop;
    const maxScrollTop = container.scrollHeight - container.clientHeight;
    const isAtBottom = maxScrollTop - currentScrollTop <= threshold;
    return isAtBottom;
  };

  // Handle scroll events to determine if we should auto-scroll
  const handleScroll = () => {
    // Debounce scroll events to avoid excessive state updates
    clearTimeout(handleScroll.timeoutId);
    handleScroll.timeoutId = setTimeout(() => {
      const nearBottom = isNearBottom();
      setShouldAutoScroll(nearBottom);
    }, 100);
  };

  const scrollToBottom = (force = false) => {
    if (force || shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end',
        inline: 'nearest'
      });
    }
  };

  // Gentle scroll for chat switches - doesn't force scroll if user has scrolled up
  const scrollToBottomGently = () => {
    // Only scroll if the container exists and user hasn't manually scrolled up significantly
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      const isSignificantlyScrolledUp = container.scrollHeight - container.scrollTop - container.clientHeight > 200;
      
      if (!isSignificantlyScrolledUp) {
        messagesEndRef.current?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'end',
          inline: 'nearest'
        });
      }
    }
  };

  const scrollToBottomIfNeeded = () => {
    if (shouldAutoScroll && isNearBottom()) {
      requestAnimationFrame(() => {
        scrollToBottom();
      });
    }
  };

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) {
      return;
    }

    try {
      // Always enable auto-scroll when user sends a message
      setShouldAutoScroll(true);
      
      // Use the chatStore's sendMessage function which handles database operations
      await sendMessage(messageText, currentChat?.id);
      
      // Force scroll to bottom after a short delay to ensure message is rendered
      setTimeout(() => {
        scrollToBottom(true); // force = true to ensure scroll happens
      }, 100);
    } catch (error) {
      console.error('Error sending message:', error);
      // Error handling is done in the chatStore
    }
  };

  const generateChatTitle = (firstMessage) => {
    const words = firstMessage.trim().split(' ').slice(0, 4);
    return words.join(' ') + (firstMessage.split(' ').length > 4 ? '...' : '');
  };

  const handleResetChat = async () => {
    if (!currentChat) return;
    
    try {
      // Reset chat by deleting and creating a new one
      await deleteChat(currentChat.id);
    } catch (error) {
      console.error('Error resetting chat:', error);
    }
  };
  
  const handleDeleteChat = async () => {
    if (!currentChat) return;
    
    try {
      await deleteChat(currentChat.id);
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  const handleUpdateChat = async (updatedChat) => {
    if (!updatedChat) return;
    
    try {
      // Map frontend field names to backend field names
      const backendUpdates = {
        title: updatedChat.title,
        is_pinned: updatedChat.pinned,
        is_archived: updatedChat.archived,
        model_name: updatedChat.model_name
      };
      
      console.log('Updating chat with backend fields:', backendUpdates);
      await updateChat(updatedChat.id, backendUpdates);
    } catch (error) {
      console.error('Error updating chat:', error);
    }
  };

  const handleDuplicateChat = async (chatToDuplicate) => {
    if (!chatToDuplicate) return;
    
    try {
      // Create a new chat with the same messages but different title
      const duplicatedChat = {
        title: `${chatToDuplicate.title} (Copy)`,
        messages: chatToDuplicate.messages || [],
        createdAt: new Date().toISOString(),
        pinned: false,
        archived: false
      };
      
      // Note: You might need to implement a proper duplicate method in the chat store
      console.log('Duplicating chat:', duplicatedChat);
      // For now, just log it - you'll need to implement the actual duplication logic
    } catch (error) {
      console.error('Error duplicating chat:', error);
    }
  };

  const handleSystemMessage = async (message) => {
    if (!currentChat) {
      console.log('System message:', message);
      // Show a temporary notification when no chat is active
      // You could implement a toast notification here
      return;
    }
    
    try {
      console.log('Adding system message to chat:', currentChat.id, message);
      // Use the sendMessage function to send a system message
      // This will persist it to the database as part of the chat history
      await sendMessage(message, currentChat.id, 'system');
      
      // Force a re-render to ensure the system message appears immediately
      setForceRefresh(prev => prev + 1);
      
      // Force scroll to bottom to show the system message
      setTimeout(() => {
        scrollToBottom(true);
      }, 100);
    } catch (error) {
      console.error('Error adding system message:', error);
      // No fallback needed since system messages are now persisted
    }
  };

  // Show empty state if there's no current chat and we're not loading
  // Also show empty state during initial loading to prevent input flicker
  if (!currentChat && (!isLoading || connectionStatus === 'connecting')) {
    return (
      <div className="chat-area empty">
        <div className="empty-state">
          <div className="empty-content">
            <div className="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-primary">Welcome to Chat</h2>
            <p className="text-base text-secondary">Select a chat from the sidebar or create a new one to get started.</p>
            <div className="features-list">
              <div className="feature">
                <div className="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
                  </svg>
                </div>
                <span className="text-sm">AI-powered conversations</span>
              </div>
              <div className="feature">
                <div className="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                  </svg>
                </div>
                <span className="text-sm">Organized chat history</span>
              </div>
              <div className="feature">
                <div className="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="M21 21l-4.35-4.35"></path>
                  </svg>
                </div>
                <span className="text-sm">Search conversations</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Get messages from the current chat, with fallback to store messages
  const chatMessages = currentChat?.messages || getActiveMessages() || [];
  
  // All messages are now persisted in chatMessages (including system messages)
  // Include forceRefresh to trigger re-renders when needed
  const allMessages = chatMessages.sort((a, b) => 
    new Date(a.timestamp || a.created_at) - new Date(b.timestamp || b.created_at)
  );
  
  // Use forceRefresh to ensure re-renders when system messages are added
  // eslint-disable-next-line no-unused-vars
  const _forceRefresh = forceRefresh;

  return (
    <div className="chat-area">
      <ChatHeader 
        chat={currentChat}
        onToggleSidebar={onToggleSidebar}
        onResetChat={handleResetChat}
        onUpdateChat={handleUpdateChat}
        onDeleteChat={handleDeleteChat}
        onDuplicateChat={handleDuplicateChat}
        onSystemMessage={handleSystemMessage}
        sidebarOpen={sidebarOpen}
        isMobile={isMobile}
      />
      
      <div 
        className="messages-container scrollbar-custom"
        ref={messagesContainerRef}
        onScroll={handleScroll}
      >
        {allMessages.length === 0 ? (
          <div className="welcome-message">
            <div className="welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-medium text-primary">Start the conversation</h3>
            <p className="text-sm text-secondary">Send a message to begin chatting with the AI assistant.</p>
          </div>
        ) : (
          allMessages.map((message, index) => {
            // Debug logging for all messages
            if (message.role === 'system') {
              console.log('System message in ChatArea:', {
                id: message.id,
                content: message.content,
                role: message.role,
                timestamp: message.timestamp || message.created_at,
                fullMessage: message
              });
            }
            
            // Use stable keys with fallback to index for temporary messages
            const messageKey = message.id || `temp-${index}-${message.timestamp || message.created_at}`;
            
            return (
              <ChatMessage
                key={messageKey}
                message={message.content}
                sender={message.role}
                timestamp={message.timestamp || message.created_at}
                isError={message.isError}
                isPending={message.isPending}
              />
            );
          })
        )}
        
        {isLoading && (
          <ChatMessage
            message=""
            sender="assistant"
            timestamp={new Date().toISOString()}
            isLoading={true}
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <InputBar 
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        placeholder="Type a message..."
        isLoading={isLoading}
      />
    </div>
  );
};

export default ChatArea;
