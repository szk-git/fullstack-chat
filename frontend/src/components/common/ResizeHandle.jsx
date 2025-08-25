import React, { useState, useCallback, useRef, useEffect } from 'react';
import './ResizeHandle.css';

const ResizeHandle = ({ onResize, minWidth = 200, maxWidth = 400, initialWidth = 280 }) => {
  const [isResizing, setIsResizing] = useState(false);
  const [width, setWidth] = useState(initialWidth);
  const handleRef = useRef(null);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!isResizing) return;

    const newWidth = e.clientX;
    const constrainedWidth = Math.min(Math.max(newWidth, minWidth), maxWidth);
    
    setWidth(constrainedWidth);
    if (onResize) {
      onResize(constrainedWidth);
    }
  }, [isResizing, minWidth, maxWidth, onResize]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div
      ref={handleRef}
      className={`resize-handle ${isResizing ? 'resizing' : ''}`}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize sidebar"
    >
      <div className="resize-handle-line" />
    </div>
  );
};

export default ResizeHandle;
