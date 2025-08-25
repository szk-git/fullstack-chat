import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/api';
import './CompactModelSelector.css';

const CompactModelSelector = ({ onModelChange }) => {
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadModels();
    loadCurrentModel();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showDropdown]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAIModels();
      setModels(response.models || []);
    } catch (err) {
      setError('Failed to load models');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
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
    console.log('handleModelSwitch called with:', modelId);
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.switchModel(modelId);
      setCurrentModel(response.current_model);
      
      // Notify parent component
      if (onModelChange) {
        onModelChange(response.current_model);
      }
      
      setShowDropdown(false);
      console.log('Model switched successfully:', response.message);
    } catch (err) {
      setError(err.message || 'Failed to switch model');
      console.error('Error switching model:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentModelData = models.find(model => model.id === currentModel);
  const availableModels = models.filter(model => model.is_loaded);

  console.log('CompactModelSelector render:', {
    models: models.length,
    currentModel,
    currentModelData: currentModelData?.name,
    availableModels: availableModels.length,
    loading,
    showDropdown,
    error
  });

  return (
    <div className="compact-model-selector" ref={dropdownRef}>
      <button
        className="model-selector-button"
        onClick={() => {
          console.log('Model selector button clicked, showDropdown:', showDropdown, 'availableModels:', availableModels.length);
          setShowDropdown(!showDropdown);
        }}
        disabled={loading || availableModels.length === 0}
        title="Select AI Model"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 12h6M9 16h6M9 8h6M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Z"/>
        </svg>
        <span className="model-name">
          {loading ? 'Loading...' : (currentModelData?.name || 'Select Model')}
        </span>
        <svg 
          className={`dropdown-arrow ${showDropdown ? 'open' : ''}`} 
          width="12" 
          height="12" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <polyline points="6,9 12,15 18,9"></polyline>
        </svg>
      </button>

      {showDropdown && (
        <div className="model-dropdown">
          {availableModels.length === 0 ? (
            <div className="dropdown-message">No models available</div>
          ) : (
            availableModels.map((model) => (
              <button
                key={model.id}
                className={`model-option ${currentModel === model.id ? 'active' : ''}`}
                onClick={() => handleModelSwitch(model.id)}
                disabled={loading}
              >
                <div className="model-info">
                  <div className="model-name">{model.name}</div>
                  <div className="model-type">{model.type}</div>
                </div>
                {currentModel === model.id && (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20,6 9,17 4,12"></polyline>
                  </svg>
                )}
              </button>
            ))
          )}
        </div>
      )}

      {error && (
        <div className="error-tooltip">
          {error}
        </div>
      )}
    </div>
  );
};

export default CompactModelSelector;
