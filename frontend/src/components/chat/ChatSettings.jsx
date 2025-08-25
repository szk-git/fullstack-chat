import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api';
import Alert from '../ui/Alert';
import './ChatSettings.css';

const ChatSettings = ({ chatId, isOpen, onClose, onSettingsChange }) => {
  const [settings, setSettings] = useState({
    temperature: '0.7',
    max_tokens: 1000,
    system_prompt: ''
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showSuccessAlert, setShowSuccessAlert] = useState(false);

  useEffect(() => {
    // Reset all states when modal opens/closes
    setShowSuccessAlert(false);
    setError(null);
    setSaving(false);
    
    if (isOpen && chatId) {
      loadSettings();
    }
  }, [isOpen, chatId]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Loading settings for chat:', chatId);
      const response = await apiClient.getChatSettings(chatId);
      console.log('Settings response:', response);
      setSettings({
        temperature: response.temperature || '0.7',
        max_tokens: response.max_tokens || 1000,
        system_prompt: response.system_prompt || ''
      });
    } catch (err) {
      console.error('Error loading settings:', err);
      // If it's a 404, that means settings don't exist yet - create defaults
      if (err.message.includes('404')) {
        setSettings({
          temperature: '0.7',
          max_tokens: 1000,
          system_prompt: ''
        });
        setError(null);
      } else {
        setError(`Failed to load settings: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setShowSuccessAlert(false); // Ensure alert is reset before save
      
      const updateData = {
        temperature: settings.temperature,
        max_tokens: parseInt(settings.max_tokens, 10),
        system_prompt: settings.system_prompt || null
      };

      console.log('Saving chat settings:', updateData);
      await apiClient.updateChatSettings(chatId, updateData);
      console.log('Chat settings saved successfully');
      
      // Show success alert only after successful save
      setShowSuccessAlert(true);
      
      // Notify parent component about settings change
      if (onSettingsChange) {
        onSettingsChange(updateData);
      }
      
      // Close modal after a brief delay to show the success message
      setTimeout(() => {
        setShowSuccessAlert(false);
        onClose();
      }, 1500);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };


  if (!isOpen) return null;

  return (
    <>
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal chat-settings-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Chat Settings</h3>
            <button 
              className="btn btn-icon close-modal"
              onClick={onClose}
              aria-label="Close settings"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div className="modal-content">
          {loading ? (
            <div className="loading-message">
              <div className="loading-spinner"></div>
              <p>Loading settings...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="error-message">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                  </svg>
                  {error}
                </div>
              )}

              <div className="settings-section">
                <label className="setting-label">
                  Temperature
                  <span className="setting-description">Controls randomness (0.1 = focused, 1.0 = creative)</span>
                </label>
                <div className="setting-input-group">
                  <input
                    type="range"
                    min="0.1"
                    max="2.0"
                    step="0.1"
                    value={settings.temperature}
                    onChange={(e) => handleInputChange('temperature', e.target.value)}
                    className="setting-slider"
                  />
                  <input
                    type="number"
                    min="0.1"
                    max="2.0"
                    step="0.1"
                    value={settings.temperature}
                    onChange={(e) => handleInputChange('temperature', e.target.value)}
                    className="setting-number"
                  />
                </div>
              </div>

              <div className="settings-section">
                <label className="setting-label">
                  Max Tokens
                  <span className="setting-description">Maximum length of the response</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="4000"
                  value={settings.max_tokens}
                  onChange={(e) => handleInputChange('max_tokens', e.target.value)}
                  className="setting-input"
                />
              </div>

              <div className="settings-section">
                <label className="setting-label">
                  System Prompt
                  <span className="setting-description">Instructions for the AI model's behavior</span>
                </label>
                <textarea
                  value={settings.system_prompt}
                  onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                  className="setting-textarea"
                  placeholder="Enter system prompt (optional)..."
                  rows={4}
                />
              </div>

            </>
          )}
        </div>

        <div className="modal-footer">
          <button 
            type="button"
            className="btn btn-secondary" 
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </button>
          <button 
            type="button"
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={loading || saving}
          >
            {saving ? (
              <>
                <div className="loading-spinner"></div>
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>
        </div>
      </div>
    </div>
      
      {showSuccessAlert && (
        <Alert 
          type="success" 
          message="Settings saved successfully" 
          onClose={() => setShowSuccessAlert(false)}
          duration={2000}
        />
      )}
    </>
  );
};

export default ChatSettings;
