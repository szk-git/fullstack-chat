import React, { useState, useRef, useEffect } from 'react';
import './InputBar.css';

const InputBar = ({ onSendMessage, disabled = false, isLoading = false }) => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !disabled) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleContainerClick = (e) => {
    // Only focus if clicking on the container itself, not on child elements
    if (e.target.classList.contains('input-container') || e.target.closest('.input-container') === e.currentTarget) {
      textareaRef.current?.focus();
    }
  };

  // Calculate character count styling
  const getCharacterCountClass = () => {
    const length = inputValue.length;
    if (length > 900) return 'character-count danger';
    if (length > 800) return 'character-count warning';
    return 'character-count';
  };

  return (
    <form className={`input-bar ${isLoading ? 'loading' : ''}`} onSubmit={handleSubmit}>
      <div className="input-container" onClick={handleContainerClick}>
        <textarea
          ref={textareaRef}
          className="message-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder={disabled ? (isLoading ? "Generating response..." : "Connection error - please check backend") : "Type your message..."}
          disabled={disabled}
          rows={1}
          maxLength={1000}
        />
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !inputValue.trim()}
          title="Send message"
        >
          <svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
          </svg>
        </button>
      </div>
      <div className="input-footer">
        <small className={getCharacterCountClass()}>
          {inputValue.length}/1000
        </small>
      </div>
    </form>
  );
};

export default InputBar;
