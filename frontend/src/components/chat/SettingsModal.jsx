import React from 'react';
import ModelSelector from './ModelSelector';
import './SettingsModal.css';

const SettingsModal = ({ isOpen, onClose, chat }) => {

  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal modal-content">
        <div className="modal-header">
          <h2 className="text-xl font-semibold">Settings</h2>
          <button 
            className="btn btn-icon close-modal"
            onClick={onClose}
            aria-label="Close settings"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div className="modal-body">
          <div className="setting-group">
            <ModelSelector />
          </div>

          {chat && (
            <div className="setting-group">
              <h3 className="setting-title text-base font-medium">Chat Info</h3>
              <div className="chat-details">
                <div className="detail-item">
                  <span className="detail-label text-sm text-secondary">Messages:</span>
                  <span className="detail-value text-sm">{chat.messages ? chat.messages.length : 0}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label text-sm text-secondary">Created:</span>
                  <span className="detail-value text-sm">{new Date(chat.createdAt).toLocaleDateString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label text-sm text-secondary">Status:</span>
                  <span className="detail-value text-sm">
                    {chat.pinned && <span className="status-badge pinned">Pinned</span>}
                    {chat.archived && <span className="status-badge archived">Archived</span>}
                    {!chat.pinned && !chat.archived && <span className="status-badge normal">Normal</span>}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsModal
