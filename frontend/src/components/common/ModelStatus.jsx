import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api';
import './ModelStatus.css';

const ModelStatus = ({ onModelChange, currentModel = null, compact = false }) => {
  const [modelStatus, setModelStatus] = useState({
    api_healthy: false,
    models: [],
    loading: true,
    error: null
  });
  
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [switchingModel, setSwitchingModel] = useState(null);

  useEffect(() => {
    fetchModelStatus();
    // Poll for status updates every 30 seconds
    const interval = setInterval(fetchModelStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchModelStatus = async () => {
    try {
      setModelStatus(prev => ({ ...prev, loading: true, error: null }));
      
      // Use the new API methods
      const [health, models] = await Promise.all([
        apiClient.healthCheck(),
        apiClient.getModels()
      ]);
      
      setModelStatus({
        api_healthy: health.status === 'healthy',
        models: models.models || [],
        loading: false,
        error: null
      });
    } catch (error) {
      setModelStatus(prev => ({
        ...prev,
        loading: false,
        error: error.message
      }));
    }
  };

  const handleModelSwitch = async (modelId) => {
    if (switchingModel || modelId === getCurrentLoadedModel()?.id) {
      return;
    }

    try {
      setSwitchingModel(modelId);
      await apiClient.loadModel(modelId);
      
      // Refresh status after switching
      await fetchModelStatus();
      
      if (onModelChange) {
        const switchedModel = modelStatus.models.find(m => m.id === modelId);
        onModelChange(switchedModel);
      }
      
      setIsDropdownOpen(false);
    } catch (error) {
      console.error('Failed to switch model:', error);
      // Optionally show error notification
    } finally {
      setSwitchingModel(null);
    }
  };

  const getCurrentLoadedModel = () => {
    return modelStatus.models.find(model => model.is_loaded) || null;
  };

  const getStatusIcon = (model) => {
    if (switchingModel === model.id) {
      return (
        <div className="status-icon loading">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21,12a9,9 0 1 1-6.219-8.56"/>
          </svg>
        </div>
      );
    }

    if (model.is_loaded) {
      return (
        <div className="status-icon ready">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="l9 12 2 2 4-4"/>
          </svg>
        </div>
      );
    }

    return (
      <div className="status-icon available">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
        </svg>
      </div>
    );
  };

  const getConnectionStatus = () => {
    if (modelStatus.loading) {
      return { status: 'loading', text: 'Checking models...', color: 'text-tertiary' };
    }
    
    if (modelStatus.error || !modelStatus.api_healthy) {
      return { status: 'error', text: 'Connection error', color: 'text-error' };
    }

    const loadedModel = getCurrentLoadedModel();
    if (loadedModel) {
      return { 
        status: 'ready', 
        text: compact ? loadedModel.id : `Ready: ${loadedModel.name}`, 
        color: 'text-success' 
      };
    }

    return { status: 'no-model', text: 'No model loaded', color: 'text-warning' };
  };

  const connectionStatus = getConnectionStatus();

  if (compact) {
    return (
      <div className="model-status-compact">
        <div className={`status-indicator ${connectionStatus.status}`}>
          <span className={`status-dot ${connectionStatus.status}`}></span>
          <span className={`status-text text-xs ${connectionStatus.color}`}>
            {connectionStatus.text}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="model-status">
      <div 
        className="model-selector"
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
      >
        <div className="current-status">
          <div className={`status-indicator ${connectionStatus.status}`}>
            <span className={`status-dot ${connectionStatus.status}`}></span>
            <div className="status-info">
              <span className={`status-text text-sm font-medium ${connectionStatus.color}`}>
                {connectionStatus.text}
              </span>
              {modelStatus.models.length > 0 && (
                <span className="text-xs text-tertiary">
                  {modelStatus.models.length} models available
                </span>
              )}
            </div>
          </div>
          
          {modelStatus.models.length > 0 && (
            <svg 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
              className={`dropdown-arrow ${isDropdownOpen ? 'open' : ''}`}
            >
              <polyline points="6,9 12,15 18,9"></polyline>
            </svg>
          )}
        </div>
      </div>

      {isDropdownOpen && modelStatus.models.length > 0 && (
        <div className="model-dropdown">
          <div className="dropdown-header">
            <h4 className="text-sm font-semibold text-primary">Available Models</h4>
            <button 
              className="btn btn-icon close-dropdown"
              onClick={() => setIsDropdownOpen(false)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          
          <div className="model-list">
            {modelStatus.models.map(model => (
              <button
                key={model.id}
                className={`model-item ${model.is_loaded ? 'active' : ''}`}
                onClick={() => handleModelSwitch(model.id)}
                disabled={switchingModel === model.id}
              >
                {getStatusIcon(model)}
                <div className="model-info">
                  <div className="model-name text-sm font-medium">
                    {model.name}
                  </div>
                  <div className="model-meta text-xs text-secondary">
                    {model.type} • {model.memory_req}
                  </div>
                </div>
                {model.is_loaded && (
                  <span className="active-badge text-xs">Active</span>
                )}
              </button>
            ))}
          </div>
          
          <div className="dropdown-footer">
            <button 
              className="btn btn-secondary refresh-button text-xs"
              onClick={fetchModelStatus}
              disabled={modelStatus.loading}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23,4 23,10 17,10"></polyline>
                <polyline points="1,20 1,14 7,14"></polyline>
                <path d="M20.49,9A9,9,0,0,0,5.64,5.64L1,10m22,4L18.36,18.36A9,9,0,0,1,3.51,15"></path>
              </svg>
              Refresh
            </button>
          </div>
        </div>
      )}
      
      {/* Click outside to close */}
      {isDropdownOpen && (
        <div 
          className="dropdown-overlay"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
};

export default ModelStatus;
