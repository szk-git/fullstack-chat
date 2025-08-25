import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/api';
import ChatSettings from './ChatSettings';
import DeleteConfirmationModal from './DeleteConfirmationModal';
import './ChatHeader.css';

const ChatHeader = ({ chat, onToggleSidebar, onResetChat, onUpdateChat, onDeleteChat, onDuplicateChat, sidebarOpen, isMobile, onSystemMessage }) => {
  const [showActions, setShowActions] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  const [modelLoading, setModelLoading] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const actionsMenuRef = useRef(null);

  // Load models and current model on component mount
  useEffect(() => {
    loadModels();
    loadCurrentModel();
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (actionsMenuRef.current && !actionsMenuRef.current.contains(event.target)) {
        setShowActions(false);
      }
    };

    if (showActions) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showActions]);

  const loadModels = async () => {
    try {
      const response = await apiClient.getAIModels();
      setModels(response.models || []);
    } catch (err) {
      console.error('Error loading models:', err);
    }
  };

  const loadCurrentModel = async () => {
    try {
      const response = await apiClient.getCurrentModel();
      setCurrentModel(response.current_model);
    } catch (err) {
      console.error('Error loading current model:', err);
    }
  };

  const handleModelSwitch = async (modelId) => {
    if (modelLoading || modelId === currentModel) {
      return;
    }

    try {
      setModelLoading(true);
      const response = await apiClient.switchModel(modelId);
      setCurrentModel(response.current_model);
      setShowModelSelector(false);
      setShowActions(false);
      
      // Update the chat's model field in the database
      if (chat && onUpdateChat) {
        const updatedChat = { ...chat, model_name: modelId };
        await onUpdateChat(updatedChat);
      }
      
      // Add system message about model change
      if (onSystemMessage) {
        const modelName = models.find(m => m.id === modelId)?.name || modelId;
        onSystemMessage(`🤖 Switched to ${modelName}`);
      }
    } catch (err) {
      console.error('Error switching model:', err);
      
      // Add error system message
      if (onSystemMessage) {
        onSystemMessage(`❌ Failed to switch model: ${err.message}`);
      }
    } finally {
      setModelLoading(false);
    }
  };

  const handleShowModelSelector = () => {
    setShowModelSelector(true);
    setShowActions(false);
  };

  if (!chat) return null;

  const handleExportChat = () => {
    const messages = chat.messages || [];
    if (messages.length === 0) {
      alert('No messages to export');
      return;
    }

    // Create chat export data
    const exportData = {
      title: chat.title,
      created_at: chat.createdAt,
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      }))
    };

    // Convert to JSON and create downloadable file
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    // Create download link
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat-${chat.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    setShowActions(false);
  };

  const handleResetChat = () => {
    if (!confirm('Are you sure you want to clear all messages in this chat? This action cannot be undone.')) {
      return;
    }

    if (onResetChat) {
      onResetChat();
    }
    setShowActions(false);
  };

  const handleRename = () => {
    setEditTitle(chat.title);
    setIsRenaming(true);
    setShowActions(false);
  };

  const handleRenameSubmit = () => {
    console.log('handleRenameSubmit called with editTitle:', editTitle);
    if (editTitle.trim() && editTitle.trim() !== chat.title) {
      console.log('Updating chat title from:', chat.title, 'to:', editTitle.trim());
      onUpdateChat({ ...chat, title: editTitle.trim() });
    }
    setIsRenaming(false);
    setEditTitle('');
  };

  const handleRenameCancel = () => {
    setIsRenaming(false);
    setEditTitle('');
  };

  const handlePin = () => {
    onUpdateChat({ ...chat, pinned: !chat.pinned });
    setShowActions(false);
  };

  const handleArchive = () => {
    onUpdateChat({ ...chat, archived: !chat.archived });
    setShowActions(false);
  };

  const handleDuplicate = () => {
    if (onDuplicateChat) {
      onDuplicateChat(chat);
    }
    setShowActions(false);
  };

  const handleDelete = () => {
    setShowDeleteConfirm(true);
    setShowActions(false);
  };

  const handleDeleteConfirm = () => {
    if (onDeleteChat) {
      onDeleteChat(chat.id);
    }
    setShowDeleteConfirm(false);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <>
      <header className="chat-header">
        <div className="header-left">
          {isMobile && !sidebarOpen && (
            <button 
              className="btn btn-icon sidebar-toggle"
              onClick={onToggleSidebar}
              aria-label="Open sidebar"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
          )}
          
          <div className="chat-info">
            <h1 className="chat-title text-lg font-semibold">{chat.title}</h1>
            <div className="chat-meta">
              <span className="message-count text-xs text-secondary">
                {chat.messages ? chat.messages.length : 0} messages
              </span>
            </div>
          </div>
        </div>

        <div className="header-right">
          <div className="header-actions">
            <button 
              className="btn btn-icon actions-button"
              onClick={() => setShowActions(!showActions)}
              aria-label="More actions"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="1"></circle>
                <circle cx="12" cy="5" r="1"></circle>
                <circle cx="12" cy="19" r="1"></circle>
              </svg>
            </button>
          </div>

          {showActions && (
            <div className="actions-menu" ref={actionsMenuRef}>
              <button className="action-item" onClick={handleShowModelSelector}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 12h6M9 16h6M9 8h6M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Z"/>
                </svg>
                <span>Change Model</span>
                <svg 
                  width="12" 
                  height="12" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2"
                  className="dropdown-icon"
                  style={{ transform: showModelSelector ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
                >
                  <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
              </button>
              
              <button className="action-item" onClick={() => { setShowSettings(true); setShowActions(false); }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M12 1v6m0 14v6m11-5l-6-6m-14 0l6 6m9-3h-6m-14 0h6"></path>
                </svg>
                <span>Chat Settings</span>
                <div className="dropdown-spacer"></div>
              </button>
              
              <hr className="action-divider" />
              
              <button className="action-item" onClick={handleExportChat}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14,2H6a2,2 0,0 0,-2,2V20a2,2 0,0 0,2,2H18a2,2 0,0 0,2,-2V8Z"></path>
                  <polyline points="14,2 14,8 20,8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10,9 9,9 8,9"></polyline>
                </svg>
                <span>Export Chat</span>
                <div className="dropdown-spacer"></div>
              </button>
              <button className="action-item" onClick={handleRename}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 20h9"></path>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
                <span>Rename Chat</span>
                <div className="dropdown-spacer"></div>
              </button>
              <button className="action-item" onClick={handlePin}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  {chat.pinned ? (
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  ) : (
                    <path d="m9 12 2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
                  )}
                </svg>
                <span>{chat.pinned ? 'Unpin Chat' : 'Pin Chat'}</span>
                <div className="dropdown-spacer"></div>
              </button>
              <button className="action-item" onClick={handleArchive}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="21,8 21,21 3,21 3,8"></polyline>
                  <rect x="1" y="3" width="22" height="5"></rect>
                  <line x1="10" y1="12" x2="14" y2="12"></line>
                </svg>
                <span>{chat.archived ? 'Unarchive Chat' : 'Archive Chat'}</span>
                <div className="dropdown-spacer"></div>
              </button>
              
              <hr className="action-divider" />
              
              <button className="action-item danger" onClick={handleDelete}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3,6 5,6 21,6"></polyline>
                  <path d="M19,6V20a2,2 0,0 1,-2,2H7a2,2 0,0 1,-2,-2V6M8,6V4a2,2 0,0 1,2,-2h4a2,2 0,0 1,2,2V6"></path>
                  <line x1="10" y1="11" x2="10" y2="17"></line>
                  <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
                <span>Delete Chat</span>
                <div className="dropdown-spacer"></div>
              </button>
            </div>
          )}
        </div>
      </header>
      
      {isRenaming && (
        <div className="modal-backdrop" onClick={handleRenameCancel}>
          <div className="modal rename-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Rename Chat</h3>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleRenameSubmit();
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  handleRenameCancel();
                }
              }}
              className="rename-input"
              placeholder="Enter chat title..."
              autoFocus
              maxLength={100}
            />
            <div className="modal-actions">
              <button 
                type="button"
                className="btn btn-secondary" 
                onMouseDown={() => console.log('Cancel button mousedown')}
                onClick={() => {
                  console.log('Cancel button clicked');
                  handleRenameCancel();
                }}
              >
                Cancel
              </button>
              <button 
                type="button"
                className="btn btn-primary" 
                onMouseDown={() => console.log('Save button mousedown')}
                onClick={() => {
                  console.log('Save button clicked');
                  handleRenameSubmit();
                }}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
      
      {showModelSelector && (
        <div className="modal-backdrop" onClick={() => setShowModelSelector(false)}>
          <div className="modal model-selector-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select AI Model</h3>
              <button 
                className="btn btn-icon close-modal"
                onClick={() => setShowModelSelector(false)}
                aria-label="Close modal"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="model-list">
              {models.length === 0 ? (
                <div className="no-models-message">
                  <p>No models available</p>
                </div>
              ) : (
                models.filter(model => model.is_loaded).map((model) => (
                  <button
                    key={model.id}
                    className={`model-item ${currentModel === model.id ? 'active' : ''}`}
                    onClick={() => handleModelSwitch(model.id)}
                    disabled={modelLoading}
                  >
                    <div className="model-info">
                      <div className="model-name">{model.name}</div>
                      <div className="model-details">
                        <span className="model-type">{model.type}</span>
                        <span className="model-memory">{model.memory_req}</span>
                      </div>
                    </div>
                    <div className="model-status">
                      {modelLoading && currentModel === model.id ? (
                        <div className="loading-spinner"></div>
                      ) : currentModel === model.id ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20,6 9,17 4,12"></polyline>
                        </svg>
                      ) : null}
                    </div>
                  </button>
                ))
              )}
            </div>
            
            {currentModel && (
              <div className="current-model-info">
                <span className="text-sm text-secondary">
                  Current model: {models.find(m => m.id === currentModel)?.name || currentModel}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
      
      <ChatSettings
        chatId={chat?.id}
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onSettingsChange={(settings) => {
          // Settings change handled by ChatSettings component
          console.log('Chat settings updated:', settings);
        }}
      />
      
      <DeleteConfirmationModal
        isOpen={showDeleteConfirm}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        title="Delete Chat"
        message="Are you sure you want to delete this chat?"
        subMessage="This action cannot be undone and all messages will be permanently lost."
        confirmText="Delete"
        cancelText="Cancel"
      />
    </>
  );
};

export default ChatHeader;
