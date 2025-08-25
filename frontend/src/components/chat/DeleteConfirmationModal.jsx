import React from 'react';
import './DeleteConfirmationModal.css';

const DeleteConfirmationModal = ({ 
  isOpen, 
  onConfirm, 
  onCancel, 
  title = "Delete Chat",
  message = "Are you sure you want to delete this chat?",
  subMessage = "This action cannot be undone.",
  confirmText = "Delete",
  cancelText = "Cancel"
}) => {
  if (!isOpen) return null;

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    } else if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      onConfirm();
    }
  };

  React.useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  return (
    <div className="modal-backdrop delete-modal-backdrop" onClick={onCancel}>
      <div className="modal delete-confirmation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="delete-modal-header">
          <div className="delete-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="M19,6V20a2,2 0,0 1,-2,2H7a2,2 0,0 1,-2,-2V6M8,6V4a2,2 0,0 1,2,-2h4a2,2 0,0 1,2,2V6"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </div>
          <h3>{title}</h3>
        </div>
        
        <div className="delete-modal-content">
          <p className="delete-message">{message}</p>
          {subMessage && <p className="delete-sub-message">{subMessage}</p>}
        </div>
        
        <div className="delete-modal-actions">
          <button 
            type="button"
            className="btn btn-secondary" 
            onClick={onCancel}
            autoFocus
          >
            {cancelText}
          </button>
          <button 
            type="button"
            className="btn btn-danger" 
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;
