import React, { useState, useEffect, useCallback } from 'react';
import ChatList from './ChatList';
import NewChatButton from './NewChatButton';
import SearchBar from './SearchBar';
import ChatFilter from './ChatFilter';
import ResizeHandle from '../common/ResizeHandle';
import useChatStore from '../../stores/chatStore';
import './ChatSidebar.css';

const ChatSidebar = ({ 
  isOpen, 
  onClose, 
  chats, 
  currentChatId, 
  onSelectChat, 
  onCreateNewChat, 
  onDeleteChat, 
  onUpdateChat,
  onDuplicateChat,
  isMobile,
  width = 280,
  onWidthChange
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const { loadChats, isFilterLoading, pendingFilterSwitch, setPendingFilterSwitch } = useChatStore();

  // Handle automatic filter switching when chat status changes
  useEffect(() => {
    if (pendingFilterSwitch && pendingFilterSwitch !== activeFilter) {
      setActiveFilter(pendingFilterSwitch);
      setPendingFilterSwitch(null); // Clear the pending switch
    }
  }, [pendingFilterSwitch, activeFilter, setPendingFilterSwitch]);

  // Reload chats when filter changes
  useEffect(() => {
    loadChats(0, activeFilter, searchTerm || null);
  }, [activeFilter, loadChats]);

  // Debounced search effect
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      loadChats(0, activeFilter, searchTerm || null);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, activeFilter, loadChats]);

  // Since we're now using database filtering, we just need to sort the chats
  // The backend already filters based on our criteria
  // Enhanced onUpdateChat to handle automatic filter switching
  const handleUpdateChat = useCallback(async (updatedChat) => {
    if (!updatedChat) return;
    
    // Check what status changed and determine target filter
    const wasArchived = updatedChat.archived === false && activeFilter === 'archived';
    const wasUnarchived = updatedChat.archived === true && activeFilter !== 'archived';
    const wasPinned = updatedChat.pinned === true && activeFilter !== 'pinned';
    const wasUnpinned = updatedChat.pinned === false && activeFilter === 'pinned';
    
    // Call the parent update function
    if (onUpdateChat) {
      await onUpdateChat(updatedChat);
    }
    
    // Handle automatic filter switching with a small delay to ensure backend update
    setTimeout(() => {
      if (wasUnarchived && updatedChat.archived) {
        // Chat was archived - switch to archived filter
        setActiveFilter('archived');
      } else if (wasArchived && !updatedChat.archived) {
        // Chat was unarchived - switch to all filter
        setActiveFilter('all');
      } else if (wasPinned && updatedChat.pinned) {
        // Chat was pinned - switch to pinned filter if not already there
        if (activeFilter !== 'pinned') {
          setActiveFilter('pinned');
        }
      } else if (wasUnpinned && !updatedChat.pinned) {
        // Chat was unpinned from pinned filter - switch to all filter
        setActiveFilter('all');
      }
    }, 150);
  }, [onUpdateChat, activeFilter]);

  const sortedChats = [...chats].sort((a, b) => {
    // Pinned chats always come first (unless we're filtering for archived)
    if (activeFilter !== 'archived') {
      const aPinned = a.pinned || a.is_pinned;
      const bPinned = b.pinned || b.is_pinned;
      
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
    }
    
    // Then sort by updated date (most recent first)
    const dateA = new Date(a.updated_at || a.created_at);
    const dateB = new Date(b.updated_at || b.created_at);
    return dateB - dateA;
  });

  return (
    <aside 
      className={`chat-sidebar ${isOpen ? 'open' : 'closed'}`}
      style={{ '--sidebar-width': `${width}px` }}
    >
      <div className="sidebar-header">
        <div className="header-top">
          <h1 className="sidebar-title text-lg font-semibold">Chats</h1>
          {isMobile && (
            <button 
              className="btn btn-icon close-sidebar"
              onClick={onClose}
              aria-label="Close sidebar"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
        
        
        <NewChatButton onClick={onCreateNewChat} />
        
        <SearchBar 
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search conversations..."
        />
        
        <ChatFilter 
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
        />
      </div>
      
      <div className={`sidebar-content ${isFilterLoading ? 'filter-loading' : ''}`}>
        <ChatList 
          chats={sortedChats}
          currentChatId={currentChatId}
          onSelectChat={onSelectChat}
          onUpdateChat={handleUpdateChat}
        />
        
        {chats.length === 0 && (
          <div className="empty-state">
            {searchTerm ? (
              <div className="text-center text-secondary">
                <p>No chats found for "{searchTerm}"</p>
              </div>
            ) : (
              <div className="welcome-empty text-center">
                <div className="welcome-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-primary">Start a conversation</h3>
                <p className="text-sm text-secondary">Create your first chat to begin</p>
              </div>
            )}
          </div>
        )}
      </div>
      
      
      {/* Resize Handle - only show on desktop */}
      {!isMobile && (
        <ResizeHandle
          onResize={onWidthChange}
          minWidth={200}
          maxWidth={400}
          initialWidth={width}
        />
      )}
    </aside>
  );
};

export default ChatSidebar;
