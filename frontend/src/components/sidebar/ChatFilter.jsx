import React from 'react';
import './ChatFilter.css';

const ChatFilter = ({ activeFilter, onFilterChange }) => {
  const filters = [
    {
      id: 'all',
      label: 'All Chats',
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/>
        </svg>
      )
    },
    {
      id: 'pinned',
      label: 'Pinned',
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2l3 10h7l-6 5 2 10-6-8-6 8 2-10-6-5h7z"/>
        </svg>
      )
    },
    {
      id: 'archived',
      label: 'Archived',
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="21,8 21,21 3,21 3,8"/>
          <rect x="1" y="3" width="22" height="5"/>
          <line x1="10" y1="12" x2="14" y2="12"/>
        </svg>
      )
    }
  ];

  return (
    <div className="chat-filter">
      <div className="filter-tabs">
        {filters.map((filter) => (
          <button
            key={filter.id}
            className={`filter-tab ${activeFilter === filter.id ? 'active' : ''}`}
            onClick={() => onFilterChange(filter.id)}
          >
            <span className="filter-icon">{filter.icon}</span>
            <span className="filter-label">{filter.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ChatFilter;
