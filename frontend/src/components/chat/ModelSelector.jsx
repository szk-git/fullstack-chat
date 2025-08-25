import React, { useState, useEffect } from 'react'
import apiClient from '../../services/api'

const ModelSelector = ({ onModelChange }) => {
  const [models, setModels] = useState([])
  const [currentModel, setCurrentModel] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadModels()
    loadCurrentModel()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      const response = await apiClient.getAIModels()
      setModels(response.models || [])
    } catch (err) {
      setError('Failed to load models')
      console.error('Error loading models:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCurrentModel = async () => {
    try {
      const response = await apiClient.getCurrentModel()
      setCurrentModel(response.current_model)
    } catch (err) {
      console.error('Error loading current model:', err)
    }
  }

  const handleModelSwitch = async (modelId) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.switchModel(modelId)
      setCurrentModel(response.current_model)
      
      // Notify parent component
      if (onModelChange) {
        onModelChange(response.current_model)
      }
      
      // Show success message (you can customize this)
      console.log('Model switched successfully:', response.message)
    } catch (err) {
      setError(err.message || 'Failed to switch model')
      console.error('Error switching model:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="model-selector">
      <div className="model-selector-header">
        <h3 className="model-selector-title">AI Model</h3>
        <p className="model-selector-description">
          Choose which AI model to use for conversations
        </p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <span>Loading models...</span>
        </div>
      ) : (
        <div className="model-options">
          {models.map((model) => (
            <div
              key={model.id}
              className={`model-option ${currentModel === model.id ? 'active' : ''} ${!model.is_loaded ? 'unavailable' : ''}`}
              onClick={() => model.is_loaded && handleModelSwitch(model.id)}
            >
              <div className="model-info">
                <div className="model-name">{model.name}</div>
                <div className="model-details">
                  <span className="model-type">{model.type}</span>
                  <span className="model-memory">{model.memory_req}</span>
                </div>
                {model.description && (
                  <div className="model-description">{model.description}</div>
                )}
              </div>
              <div className="model-status">
                {currentModel === model.id && (
                  <span className="current-indicator">Current</span>
                )}
                {!model.is_loaded && (
                  <span className="loading-indicator">Loading...</span>
                )}
                {model.is_loaded && currentModel !== model.id && (
                  <span className="available-indicator">Available</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="model-selector-footer">
        <p className="model-selector-note">
          Models are preloaded for instant switching. No delay when switching between available models.
        </p>
      </div>
    </div>
  )
}

export default ModelSelector
