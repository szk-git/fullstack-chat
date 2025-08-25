import React, { useEffect, useRef, useState } from 'react';
import ChatItem from './ChatItem';
import useChatStore from '../../stores/chatStore';
import './ChatList.css';

const ChatList = ({ chats, currentChatId, onSelectChat, onUpdateChat }) => {
  const [newChatIds, setNewChatIds] = useState(new Set());
  const [isTransitioning, setIsTransitioning] = useState(false);
  const prevChatsRef = useRef([]);
  const timeoutRef = useRef({});
  const { isFilterLoading } = useChatStore();

  useEffect(() => {
    if (!chats || chats.length === 0) {
      prevChatsRef.current = [];
      setNewChatIds(new Set());
      return;
    }

    const prevChats = prevChatsRef.current;
    const currentChatIds = new Set(chats.map(chat => chat.id));
    const prevChatIds = new Set(prevChats.map(chat => chat.id));
    
    // Find newly added chats
    const newlyAdded = chats.filter(chat => !prevChatIds.has(chat.id));
    
    if (newlyAdded.length > 0) {
      const newIds = new Set(newlyAdded.map(chat => chat.id));
      setNewChatIds(newIds);
      
      // Clear the animation class after animation completes
      newlyAdded.forEach(chat => {
        if (timeoutRef.current[chat.id]) {
          clearTimeout(timeoutRef.current[chat.id]);
        }
        
        timeoutRef.current[chat.id] = setTimeout(() => {
          setNewChatIds(prev => {
            const updated = new Set(prev);
            updated.delete(chat.id);
            return updated;
          });
          delete timeoutRef.current[chat.id];
        }, 400); // Match animation duration
      });
    }
    
    prevChatsRef.current = chats;
  }, [chats]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      Object.values(timeoutRef.current).forEach(clearTimeout);
    };
  }, []);

  // Handle transition effects during filter loading
  useEffect(() => {
    if (isFilterLoading) {
      setIsTransitioning(true);
      const timer = setTimeout(() => {
        setIsTransitioning(false);
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [isFilterLoading]);

  if (!chats || chats.length === 0) {
    return null;
  }

  return (
    <div className={`chat-list ${
      isFilterLoading || isTransitioning ? 'filter-transitioning' : ''
    }`}>
      <div className="chat-items">
        {chats.map(chat => {
          const isNewChat = newChatIds.has(chat.id);
          return (
            <div
              key={chat.id}
              className={`chat-item-wrapper ${
                isNewChat ? 'new-chat-animation' : ''
              } ${
                isFilterLoading ? 'filter-loading' : ''
              }`}
            >
              <ChatItem 
                chat={chat}
                isActive={currentChatId === chat.id}
                onSelect={() => onSelectChat(chat.id)}
                onUpdateChat={onUpdateChat}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChatList;
