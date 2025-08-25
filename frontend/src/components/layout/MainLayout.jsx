import React, { useState, useEffect } from 'react';
import ChatSidebar from '../sidebar/ChatSidebar';
import ChatArea from '../chat/ChatArea';
import storage from '../../utils/storage';
import useChatStore from '../../stores/chatStore';
import './MainLayout.css';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(storage.get('sidebarWidth', 280));
  const [isMobile, setIsMobile] = useState(false);
  
  // Use database-driven chat store
  const {
    chats,
    activeChat,
    isLoading,
    connectionStatus,
    loadChats,
    createNewChat,
    setActiveChat,
    deleteChat: deleteChatFromStore,
    loadChatMessages,
    updateChat
  } = useChatStore();

  // Check if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      // Auto-open sidebar on desktop
      if (window.innerWidth >= 1024) {
        setSidebarOpen(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Load chats from database on component mount with 'all' filter (which maps to 'active')
  useEffect(() => {
    // Set loading state to prevent flicker during initial load
    loadChats(0, 'all'); // 'all' will map to 'active' in the store
  }, [loadChats]);

  // Handle loading state to prevent UI flicker during transitions
  const isTransitioning = isLoading && !activeChat;

  // Auto-close sidebar on mobile when chat changes
  useEffect(() => {
    if (isMobile && activeChat) {
      setSidebarOpen(false);
    }
  }, [activeChat?.id, isMobile]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleCreateNewChat = async () => {
    try {
      const newChat = await createNewChat();
      if (isMobile) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleSelectChat = async (chatId) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      await setActiveChat(chat);
      // Load messages for this chat
      await loadChatMessages(chatId);
    }
    
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleDeleteChat = async (chatId) => {
    try {
      await deleteChatFromStore(chatId);
      // If deleted chat was active, reload chats and clear active chat
      if (activeChat?.id === chatId) {
        setActiveChat(null);
        await loadChats();
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  const handleDuplicateChat = async (chatId) => {
    const originalChat = chats.find(chat => chat.id === chatId);
    if (!originalChat) return;
    
    try {
      // Create new chat with initial message from original
      const initialMessage = originalChat.messages?.[0]?.content || null;
      const newChat = await createNewChat(initialMessage);
      
      if (newChat && isMobile) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Failed to duplicate chat:', error);
    }
  };

  const handleUpdateChat = async (updatedChat) => {
    if (!updatedChat) return;
    
    try {
      // Map frontend field names to backend field names
      const backendUpdates = {
        title: updatedChat.title,
        is_pinned: updatedChat.pinned,
        is_archived: updatedChat.archived
      };
      
      console.log('Updating chat with backend fields:', backendUpdates);
      await updateChat(updatedChat.id, backendUpdates);
    } catch (error) {
      console.error('Error updating chat:', error);
    }
  };

  const handleSidebarResize = (newWidth) => {
    setSidebarWidth(newWidth);
    storage.set('sidebarWidth', newWidth);
  };

  // Pass chats directly to ChatSidebar since it handles filtering and sorting

  return (
    <div className="main-layout">
      {/* Mobile overlay */}
      {sidebarOpen && isMobile && (
        <div 
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
      
      <ChatSidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chats={chats}
        currentChatId={activeChat?.id}
        onSelectChat={handleSelectChat}
        onCreateNewChat={handleCreateNewChat}
        onDeleteChat={handleDeleteChat}
        onUpdateChat={handleUpdateChat}
        onDuplicateChat={handleDuplicateChat}
        isMobile={isMobile}
        width={sidebarWidth}
        onWidthChange={handleSidebarResize}
        isLoading={isLoading}
        connectionStatus={connectionStatus}
      />
      
      <main className={`chat-main ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <ChatArea 
          currentChat={activeChat}
          onToggleSidebar={toggleSidebar}
          sidebarOpen={sidebarOpen}
          isMobile={isMobile}
          isLoading={isLoading}
          connectionStatus={connectionStatus}
        />
      </main>
    </div>
  );
};

export default MainLayout;
