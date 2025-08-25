const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.sessionId = this.generateSessionId();
  }

  generateSessionId() {
    // Try to get existing session ID from localStorage first
    const existingSessionId = localStorage.getItem('chat_session_id');
    if (existingSessionId) {
      return existingSessionId;
    }
    
    // Generate a new session ID and persist it
    const newSessionId = `session_${Math.random().toString(36).substr(2, 16)}_${Date.now()}`;
    localStorage.setItem('chat_session_id', newSessionId);
    return newSessionId;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Id': this.sessionId,
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.indexOf('application/json') !== -1) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.request('/api/v1/health');
  }

  // Legacy health check for backward compatibility
  async legacyHealthCheck() {
    return this.request('/healthz');
  }

  // Chat endpoints
  async getChats(page = 1, perPage = 50, search = null, filter = 'all') {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString()
    });
    if (search) {
      params.set('search', search);
    }
    if (filter && filter !== 'all') {
      params.set('filter', filter);
    }
    return this.request(`/api/v1/chats/?${params.toString()}`);
  }

  // Get chats filtered by status
  async getChatsByStatus(status, page = 1, perPage = 50, search = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      filter: status
    });
    if (search) {
      params.set('search', search);
    }
    return this.request(`/api/v1/chats/?${params.toString()}`);
  }

  // Get pinned chats
  async getPinnedChats(page = 1, perPage = 50) {
    return this.getChatsByStatus('pinned', page, perPage);
  }

  // Get archived chats
  async getArchivedChats(page = 1, perPage = 50) {
    return this.getChatsByStatus('archived', page, perPage);
  }

  // Get active (non-archived) chats
  async getActiveChats(page = 1, perPage = 50) {
    return this.getChatsByStatus('active', page, perPage);
  }

  async createChat(title = null, initialMessage = null) {
    return this.request('/api/v1/chats/', {
      method: 'POST',
      body: {
        title,
        initial_message: initialMessage
      },
    });
  }

  async getChat(chatId) {
    return this.request(`/api/v1/chats/${chatId}`);
  }

  async updateChat(chatId, updateData) {
    return this.request(`/api/v1/chats/${chatId}`, {
      method: 'PUT',
      body: updateData,
    });
  }

  async deleteChat(chatId) {
    return this.request(`/api/v1/chats/${chatId}`, {
      method: 'DELETE',
    });
  }

  // Message endpoints
  async sendMessageToSession(message) {
    return this.request('/api/v1/chats/messages/', {
      method: 'POST',
      body: {
        content: message,
      },
    });
  }

  async sendMessage(chatId, message) {
    return this.request(`/api/v1/chats/${chatId}/messages`, {
      method: 'POST',
      body: {
        content: message,
      },
    });
  }

  async addSystemMessage(chatId, message) {
    return this.request(`/api/v1/chats/${chatId}/system-message`, {
      method: 'POST',
      body: {
        content: message,
      },
    });
  }

  // Chat settings endpoints
  async getChatSettings(chatId) {
    return this.request(`/api/v1/chats/${chatId}/settings`);
  }

  async updateChatSettings(chatId, settings) {
    return this.request(`/api/v1/chats/${chatId}/settings`, {
      method: 'PUT',
      body: settings,
    });
  }

  async resetChat(chatId) {
    // In the new API, reset is accomplished by deleting and creating a new chat
    try {
      await this.deleteChat(chatId);
      // Generate random name for reset chat (will be handled by the store's createNewChat)
      return await this.createChat('New Chat'); // This will be overridden by random name in store
    } catch (error) {
      console.error('Error resetting chat:', error);
      throw error;
    }
  }

  // Model status endpoints
  async getModelStatus() {
    try {
      const [apiHealth, aiModels] = await Promise.all([
        this.healthCheck(),
        this.getAvailableModels()
      ]);
      return {
        api_healthy: true,
        api_status: apiHealth,
        models: aiModels.models || []
      };
    } catch (error) {
      console.error('Failed to get model status:', error);
      return {
        api_healthy: false,
        api_status: null,
        models: []
      };
    }
  }

  async getAvailableModels() {
    try {
      const response = await fetch('http://localhost:8001/models');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch AI models:', error);
      return { models: [] };
    }
  }

  async switchModel(modelId) {
    try {
      const response = await fetch(`http://localhost:8001/models/${encodeURIComponent(modelId)}/switch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to switch model:', error);
      throw error;
    }
  }

  async getAIModels() {
    return this.getAvailableModels();
  }

  async getCurrentModel() {
    try {
      const response = await fetch('http://localhost:8001/models/current');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get current model:', error);
      return { current_model: null };
    }
  }

  // Session management
  clearSession() {
    localStorage.removeItem('chat_session_id');
    this.sessionId = this.generateSessionId();
    console.log('Session cleared and new session ID generated:', this.sessionId);
  }

  getCurrentSessionId() {
    return this.sessionId;
  }

}

export const apiClient = new ApiClient();
export default apiClient;
