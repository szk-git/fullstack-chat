import React from 'react';
import './SearchBar.css';

const SearchBar = ({ value, onChange, placeholder = 'Search conversations...' }) => {
  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  const handleClear = () => {
    if (onChange) {
      onChange('');
    }
  };

  return (
    <div className="search-bar">
      <div className="search-input-wrapper">
        <svg 
          className="search-icon" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <path d="M21 21l-4.35-4.35"></path>
        </svg>
        
        <input
          type="text"
          className="search-input"
          value={value || ''}
          onChange={handleChange}
          placeholder={placeholder}
          aria-label="Search conversations"
        />
        
        {value && (
          <button
            className="clear-search"
            onClick={handleClear}
            aria-label="Clear search"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchBar;
