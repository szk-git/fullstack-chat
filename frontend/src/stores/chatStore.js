import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { apiClient } from '../services/api.js'

// Utility function to generate random chat names
const generateRandomChatName = () => {
  const adjectives = [
    'Creative', 'Brilliant', 'Curious', 'Thoughtful', 'Inspiring', 'Dynamic', 'Innovative',
    'Focused', 'Energetic', 'Productive', 'Strategic', 'Insightful', 'Collaborative',
    'Ambitious', 'Visionary', 'Efficient', 'Analytical', 'Resourceful', 'Optimistic', 'Bold'
  ];
  
  const nouns = [
    'Discussion', 'Brainstorm', 'Conversation', 'Chat', 'Dialogue', 'Meeting', 'Session',
    'Exchange', 'Talk', 'Inquiry', 'Exploration', 'Analysis', 'Workshop', 'Consultation',
    'Project', 'Journey', 'Adventure', 'Quest', 'Discovery', 'Collaboration'
  ];
  
  const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
  const noun = nouns[Math.floor(Math.random() * nouns.length)];
  
  return `${adjective} ${noun}`;
};

const useChatStore = create(
  subscribeWithSelector((set, get) => ({
    // State
    chats: [],
    activeChat: null,
    messages: {},
    isLoading: false,
    isFilterLoading: false, // Separate loading state for filter changes
    currentFilter: 'all', // Track current filter to prevent unnecessary reloads
    hasInitiallyLoaded: false, // Track if we've loaded chats at least once
    isSidebarOpen: true,
    connectionStatus: 'connecting', // connecting, connected, error
    sessionId: apiClient.sessionId,
    pendingFilterSwitch: null, // Track pending automatic filter switches

    // Actions
    setConnectionStatus: (status) => set({ connectionStatus: status }),
    
    setLoading: (loading) => set({ isLoading: loading }),
    
    toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
    
    setCurrentFilter: (filter) => set({ currentFilter: filter }),
    
    setPendingFilterSwitch: (filter) => set({ pendingFilterSwitch: filter }),
    
    setChats: (chats) => set({ chats }),
    
    addChat: (chat) => set((state) => ({
      chats: [chat, ...state.chats]
    })),
    
    updateChat: async (chatId, updates) => {
      try {
        // Update the chat on the server
        await apiClient.updateChat(chatId, updates);
        
        // Map backend fields to frontend fields for local state
        const frontendUpdates = {
          ...updates,
          pinned: updates.is_pinned !== undefined ? updates.is_pinned : updates.pinned,
          archived: updates.is_archived !== undefined ? updates.is_archived : updates.archived
        };
        
        console.log('Updating local state with:', frontendUpdates);
        
        // Check if the chat's pin/archive status changed to trigger filter updates
        const state = get();
        const currentChat = state.chats.find(chat => chat.id === chatId);
        const statusChanged = currentChat && (
          (frontendUpdates.pinned !== undefined && frontendUpdates.pinned !== currentChat.pinned) ||
          (frontendUpdates.archived !== undefined && frontendUpdates.archived !== currentChat.archived)
        );
        
        // Determine automatic filter switching logic
        let targetFilter = null;
        if (statusChanged && currentChat) {
          const wasArchived = frontendUpdates.archived === true && !currentChat.archived;
          const wasUnarchived = frontendUpdates.archived === false && currentChat.archived;
          const wasPinned = frontendUpdates.pinned === true && !currentChat.pinned;
          const wasUnpinned = frontendUpdates.pinned === false && currentChat.pinned;
          
          if (wasArchived) {
            // Chat was archived - switch to archived filter
            targetFilter = 'archived';
          } else if (wasUnarchived) {
            // Chat was unarchived - switch to all filter
            targetFilter = 'all';
          } else if (wasPinned && state.currentFilter !== 'pinned') {
            // Chat was pinned and we're not already on pinned filter - switch to pinned
            targetFilter = 'pinned';
          } else if (wasUnpinned && state.currentFilter === 'pinned') {
            // Chat was unpinned and we're on pinned filter - switch to all
            targetFilter = 'all';
          }
        }
        
        // Update local state
        set((state) => ({
          chats: state.chats.map(chat => 
            chat.id === chatId ? { ...chat, ...frontendUpdates } : chat
          ),
          activeChat: state.activeChat?.id === chatId 
            ? { ...state.activeChat, ...frontendUpdates }
            : state.activeChat,
          pendingFilterSwitch: targetFilter || state.pendingFilterSwitch
        }));
        
        // If status changed, reload chats to ensure proper filtering
        if (statusChanged) {
          // Small delay to ensure the update is processed
          setTimeout(() => {
            const newState = get();
            const filterToLoad = targetFilter || newState.currentFilter;
            newState.loadChats(0, filterToLoad, null);
          }, 100);
        }
      } catch (error) {
        console.error('Failed to update chat:', error);
        throw error;
      }
    },
    
    removeChat: (chatId) => set((state) => ({
      chats: state.chats.filter(chat => chat.id !== chatId),
      activeChat: state.activeChat?.id === chatId ? null : state.activeChat,
      messages: { ...state.messages, [chatId]: undefined }
    })),
    
    setActiveChat: async (chat) => {
      const state = get()
      
      // Auto-delete empty previous chat if switching away
      if (state.activeChat && state.activeChat.id !== chat?.id) {
        const prevChat = state.activeChat
        const prevMessages = state.messages[prevChat.id] || []
        
        // Check if chat is empty (no real messages, only temporary ones or none)
        const hasRealMessages = prevMessages.some(msg => 
          !msg.isPending && !msg.isTemp && msg.role === 'user'
        )
        
        // Auto-delete if no real interaction happened
        if (!hasRealMessages && prevChat.message_count === 0) {
          try {
            await apiClient.deleteChat(prevChat.id)
            // Remove from state without calling the full deleteChat action
            set((state) => ({
              chats: state.chats.filter(c => c.id !== prevChat.id),
              messages: { ...state.messages, [prevChat.id]: undefined }
            }))
          } catch (error) {
            console.warn('Failed to auto-delete empty chat:', error)
          }
        }
      }
      
      // Set the new active chat
      set((state) => ({
        activeChat: chat,
        // Load messages for this chat if not already loaded
        messages: chat && !state.messages[chat.id] 
          ? { ...state.messages, [chat.id]: [] }
          : state.messages
      }))
    },
    
    setMessages: (chatId, messages) => set((state) => ({
      messages: { ...state.messages, [chatId]: messages }
    })),
    
    addMessage: (chatId, message) => set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: [...(state.messages[chatId] || []), message]
      }
    })),
    
    updateMessage: (chatId, messageId, updates) => set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: (state.messages[chatId] || []).map(msg =>
          msg.id === messageId ? { ...msg, ...updates } : msg
        )
      }
    })),
    
    // Derived state getters
    getActiveMessages: () => {
      const { activeChat, messages } = get()
      return activeChat ? messages[activeChat.id] || [] : []
    },
    
    getActiveChatId: () => {
      const { activeChat } = get()
      return activeChat?.id
    },
    
    getChatById: (chatId) => {
      const { chats } = get()
      return chats.find(chat => chat.id === chatId)
    },
    
    // API-driven actions
    loadChats: async (retryCount = 0, filter = 'all', search = null) => {
      const state = get();
      
      // Skip reload if same filter and no search change, but always load on first time
      if (state.currentFilter === filter && search === null && !retryCount && state.hasInitiallyLoaded) {
        return;
      }
      
      try {
        // Use filter loading for smooth transitions, regular loading for initial load
        const isFilterChange = state.chats.length > 0 && filter !== state.currentFilter;
        set({ 
          isFilterLoading: isFilterChange,
          isLoading: !isFilterChange || retryCount > 0,
          currentFilter: filter
        });
        
        // Map frontend filter names to backend filter names
        let apiFilter = 'all';
        switch (filter) {
          case 'pinned':
            apiFilter = 'pinned';
            break;
          case 'archived':
            apiFilter = 'archived';
            break;
          case 'all':
          default:
            apiFilter = 'active'; // Show active (non-archived) chats by default
            break;
        }
        
        console.log(`Loading chats with filter: ${apiFilter}, search: ${search}`);
        const response = await apiClient.getChats(1, 50, search, apiFilter)
        
        // Map backend field names to frontend field names
        const mappedChats = (response.chats || []).map(chat => ({
          ...chat,
          pinned: chat.is_pinned || false,
          archived: chat.is_archived || false,
          // Keep original fields for API compatibility
          is_pinned: chat.is_pinned || false,
          is_archived: chat.is_archived || false
        }));
        
        set({ 
          chats: mappedChats,
          isLoading: false,
          isFilterLoading: false,
          connectionStatus: 'connected',
          hasInitiallyLoaded: true
        })
      } catch (error) {
        console.error('Failed to load chats:', error)
        
        // Retry up to 2 times with exponential backoff
        if (retryCount < 2) {
          const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s
          console.log(`Retrying connection in ${delay}ms...`)
          setTimeout(() => {
            get().loadChats(retryCount + 1, filter, search)
          }, delay)
        } else {
          set({ 
            isLoading: false,
            isFilterLoading: false,
            connectionStatus: 'error'
          })
        }
      }
    },

    loadChatMessages: async (chatId) => {
      try {
        const response = await apiClient.getChat(chatId)
        if (response) {
          // Update the active chat with the loaded messages
          set((state) => {
            const updatedChats = state.chats.map(chat => 
              chat.id === chatId 
                ? { ...chat, messages: response.messages || [] }
                : chat
            )
            
            const updatedActiveChat = state.activeChat?.id === chatId 
              ? { ...state.activeChat, messages: response.messages || [] }
              : state.activeChat

            return {
              chats: updatedChats,
              activeChat: updatedActiveChat,
              messages: {
                ...state.messages,
                [chatId]: response.messages || []
              }
            }
          })
        }
      } catch (error) {
        console.error('Failed to load chat messages:', error)
      }
    },

    createNewChat: async (initialMessage = null) => {
      const state = get()
      
      try {
        set({ isLoading: true })
        
        // Auto-delete empty current chat before creating new one
        if (state.activeChat) {
          const currentChat = state.activeChat
          const currentMessages = state.messages[currentChat.id] || []
          
          // Check if current chat is empty (no real messages, only temporary ones or none)
          const hasRealMessages = currentMessages.some(msg => 
            !msg.isPending && !msg.isTemp && msg.role === 'user'
          )
          
          // Auto-delete if no real interaction happened
          if (!hasRealMessages && currentChat.message_count === 0) {
            try {
              await apiClient.deleteChat(currentChat.id)
              // Remove from state without calling the full deleteChat action
              // Don't set activeChat to null to prevent empty state flicker
              set((state) => ({
                chats: state.chats.filter(c => c.id !== currentChat.id),
                messages: { ...state.messages, [currentChat.id]: undefined }
                // activeChat will be updated when new chat is created
              }))
            } catch (error) {
              console.warn('Failed to auto-delete empty chat before creating new:', error)
            }
          }
        }
        
        const randomName = generateRandomChatName()
        const response = await apiClient.createChat(randomName, initialMessage)
        
        if (response.chat) {
          set((state) => ({
            chats: [response.chat, ...state.chats],
            activeChat: response.chat,
            messages: {
              ...state.messages,
              [response.chat.id]: response.message ? [response.message] : []
            },
            isLoading: false
          }))
          return response.chat
        }
      } catch (error) {
        console.error('Failed to create chat:', error)
        set({ isLoading: false })
        throw error
      }
    },

    sendMessage: async (message, chatId = null, role = 'user') => {
      // Declare targetChatId in the outer scope so it's accessible in error handling
      let targetChatId = chatId
      
      try {
        set({ isLoading: true })
        
        // For system messages, use the backend API
        if (role === 'system') {
          if (!chatId) {
            console.warn('Cannot add system message without a chat ID');
            set({ isLoading: false });
            return;
          }
          
          try {
            console.log('[SYSTEM_MESSAGE] Adding system message to chat:', chatId, 'content:', message);
            
            // Call backend API to add system message
            const response = await apiClient.addSystemMessage(chatId, message);
            
            console.log('[SYSTEM_MESSAGE] Backend response:', response);
            
            if (response.system_message) {
              const systemMessage = response.system_message;
              
              console.log('[SYSTEM_MESSAGE] Processing system message:', systemMessage);
              
              // Add system message to local state with immediate update
              set((state) => {
                console.log('[SYSTEM_MESSAGE] Current state before update:', {
                  currentChatMessages: state.messages[chatId]?.length || 0,
                  activeChatMessages: state.activeChat?.messages?.length || 0
                });
                
                const updatedMessages = {
                  ...state.messages,
                  [chatId]: [...(state.messages[chatId] || []), systemMessage]
                };
                
                const updatedChats = state.chats.map(chat => 
                  chat.id === chatId 
                    ? { 
                        ...chat, 
                        messages: [...(chat.messages || []), systemMessage],
                        updated_at: systemMessage.created_at
                      }
                    : chat
                );
                
                const updatedActiveChat = state.activeChat?.id === chatId 
                  ? {
                      ...state.activeChat,
                      messages: [...(state.activeChat.messages || []), systemMessage],
                      updated_at: systemMessage.created_at
                    }
                  : state.activeChat;
                
                console.log('[SYSTEM_MESSAGE] State after update:', {
                  newChatMessages: updatedMessages[chatId]?.length || 0,
                  newActiveChatMessages: updatedActiveChat?.messages?.length || 0,
                  systemMessage: systemMessage
                });
                
                return {
                  chats: updatedChats,
                  activeChat: updatedActiveChat,
                  messages: updatedMessages,
                  isLoading: false
                };
              });
              
              console.log('[SYSTEM_MESSAGE] System message successfully added to state');
              return response;
            } else {
              console.error('[SYSTEM_MESSAGE] No system_message in response:', response);
              set({ isLoading: false });
              return response;
            }
          } catch (error) {
            console.error('Failed to add system message via API:', error);
            set({ isLoading: false });
            throw error;
          }
        }
        
        // Create temporary user message to display immediately
        const tempUserMessage = {
          id: `temp_user_${Date.now()}`,
          content: message,
          role: role,
          timestamp: new Date().toISOString(),
          created_at: new Date().toISOString(),
          isPending: true
        }
        
        // Get current state for chat management
        const currentState = get()
        
        // If no chatId provided, we need to create a new chat or use active session
        if (!chatId) {
          // For new chats, we'll use a temporary chat ID until we get the real one from the backend
          targetChatId = `temp_chat_${Date.now()}`
        }
        
        // Add the user message immediately to the UI
        set((state) => {
          let updatedChats = state.chats
          let updatedActiveChat = state.activeChat
          
          if (!chatId) {
            // Create a temporary new chat
            const tempChatData = {
              id: targetChatId,
              title: message.substring(0, 50) + (message.length > 50 ? '...' : ''),
              message_count: 1,
              created_at: tempUserMessage.created_at,
              updated_at: tempUserMessage.created_at,
              messages: [tempUserMessage],
              isPending: true
            }
            
            updatedChats = [tempChatData, ...state.chats]
            updatedActiveChat = tempChatData
          } else {
            // Add message to existing chat
            updatedChats = state.chats.map(chat => 
              chat.id === targetChatId 
                ? { 
                    ...chat, 
                    updated_at: tempUserMessage.created_at,
                    messages: [...(chat.messages || []), tempUserMessage]
                  }
                : chat
            )
            
            if (state.activeChat?.id === targetChatId) {
              updatedActiveChat = {
                ...state.activeChat,
                updated_at: tempUserMessage.created_at,
                messages: [...(state.activeChat.messages || []), tempUserMessage]
              }
            }
          }
          
          return {
            chats: updatedChats,
            activeChat: updatedActiveChat,
            messages: {
              ...state.messages,
              [targetChatId]: [...(state.messages[targetChatId] || []), tempUserMessage]
            }
          }
        })
        
        // Now make the API call
        let response
        if (chatId) {
          response = await apiClient.sendMessage(chatId, message)
        } else {
          response = await apiClient.sendMessageToSession(message)
        }
        
        if (response) {
          const realChatId = response.chat_id || chatId
          const realUserMessage = response.user_message
          const assistantMessage = response.assistant_message
          
          set((state) => {
            // Update messages in the store - replace temp message with real ones
            let currentMessages = state.messages[targetChatId] || []
            
            // Remove the temporary user message and add the real messages
            currentMessages = currentMessages.filter(msg => !msg.isPending)
            const newMessages = [realUserMessage, assistantMessage]
            
            const updatedMessages = {
              ...state.messages,
              [realChatId]: [...currentMessages, ...newMessages]
            }
            
            // Handle chat updates
            let updatedChats = state.chats
            let updatedActiveChat = state.activeChat
            
            if (!chatId) {
              // Replace temporary chat with real chat data
              const realChatData = {
                id: realChatId,
                title: realUserMessage.content.substring(0, 50) + (realUserMessage.content.length > 50 ? '...' : ''),
                message_count: response.message_count,
                created_at: realUserMessage.created_at,
                updated_at: assistantMessage.created_at,
                messages: newMessages
              }
              
              updatedChats = state.chats.map(chat => 
                chat.id === targetChatId ? realChatData : chat
              )
              updatedActiveChat = realChatData
              
              // Update messages with real chat ID if it's different
              if (realChatId !== targetChatId) {
                updatedMessages[realChatId] = updatedMessages[targetChatId]
                delete updatedMessages[targetChatId]
              }
            } else {
              // Update existing chat
              updatedChats = state.chats.map(chat => 
                chat.id === realChatId 
                  ? { 
                      ...chat, 
                      message_count: response.message_count,
                      updated_at: assistantMessage.created_at,
                      messages: [...(currentMessages), ...newMessages]
                    }
                  : chat
              )
              
              if (state.activeChat?.id === realChatId) {
                updatedActiveChat = {
                  ...state.activeChat,
                  message_count: response.message_count,
                  updated_at: assistantMessage.created_at,
                  messages: [...(currentMessages), ...newMessages]
                }
              }
            }
            
            return {
              chats: updatedChats,
              activeChat: updatedActiveChat,
              messages: updatedMessages,
              isLoading: false
            }
          })
          
          return response
        }
      } catch (error) {
        console.error('Failed to send message:', error)
        
        // On error, mark the temporary message as failed and stop loading
        set((state) => {
          // Use the targetChatId from outer scope
          const errorTargetChatId = targetChatId
          const updatedMessages = {
            ...state.messages,
            [errorTargetChatId]: (state.messages[errorTargetChatId] || []).map(msg => 
              msg.isPending ? { ...msg, isError: true, isPending: false } : msg
            )
          }
          
          // Update the chats list to show error state if it's a new chat
          const updatedChats = !chatId ? state.chats.map(chat => 
            chat.id === errorTargetChatId 
              ? { ...chat, messages: updatedMessages[errorTargetChatId] }
              : chat
          ) : state.chats.map(chat => 
            chat.id === errorTargetChatId 
              ? { ...chat, messages: updatedMessages[errorTargetChatId] }
              : chat
          )
          
          const updatedActiveChat = state.activeChat?.id === errorTargetChatId
            ? { ...state.activeChat, messages: updatedMessages[errorTargetChatId] }
            : state.activeChat
          
          return {
            chats: updatedChats,
            activeChat: updatedActiveChat,
            messages: updatedMessages,
            isLoading: false
          }
        })
        
        throw error
      }
    },

    deleteChat: async (chatId) => {
      try {
        await apiClient.deleteChat(chatId)
        set((state) => ({
          chats: state.chats.filter(chat => chat.id !== chatId),
          activeChat: state.activeChat?.id === chatId ? null : state.activeChat,
          messages: { ...state.messages, [chatId]: undefined }
        }))
      } catch (error) {
        console.error('Failed to delete chat:', error)
        throw error
      }
    },

    // Computed properties
    get activeChatMessages() {
      return this.getActiveMessages()
    },
    
    get hasActiveChat() {
      return !!get().activeChat
    },
    
    get isConnected() {
      return get().connectionStatus === 'connected'
    }
  }))
)

export default useChatStore
