import React from 'react';
import './NewChatButton.css';

const NewChatButton = ({ onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };
  
  return (
    <button 
      className="btn btn-primary new-chat-button"
      onClick={handleClick}
      aria-label="Create new chat"
    >
      <svg 
        width="18" 
        height="18" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2"
        className="new-chat-icon"
      >
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <line x1="5" y1="12" x2="19" y2="12"></line>
      </svg>
      <span className="new-chat-text text-sm font-medium">New Chat</span>
    </button>
  );
};

export default NewChatButton;
