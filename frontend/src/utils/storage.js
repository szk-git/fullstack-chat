/**
 * Clean storage utility that only stores essential UI preferences
 * No chat data or session information should be stored here
 */

const STORAGE_PREFIX = 'fullstack_chat_';

const ALLOWED_KEYS = [
  'theme',           // UI theme preference
  'sidebarWidth',    // Sidebar width preference
  'language',        // UI language preference
  'notifications',   // Notification preferences
];

export const storage = {
  // Get a value from localStorage (only for allowed keys)
  get: (key, defaultValue = null) => {
    if (!ALLOWED_KEYS.includes(key)) {
      console.warn(`Storage access denied for key: ${key}. Only UI preferences are allowed.`);
      return defaultValue;
    }
    
    try {
      const item = localStorage.getItem(STORAGE_PREFIX + key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  },

  // Set a value in localStorage (only for allowed keys)
  set: (key, value) => {
    if (!ALLOWED_KEYS.includes(key)) {
      console.warn(`Storage write denied for key: ${key}. Only UI preferences are allowed.`);
      return false;
    }
    
    try {
      if (value === undefined || value === null) {
        localStorage.removeItem(STORAGE_PREFIX + key);
      } else {
        localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
      }
      return true;
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
      return false;
    }
  },

  // Remove a value from localStorage
  remove: (key) => {
    if (!ALLOWED_KEYS.includes(key)) {
      console.warn(`Storage remove denied for key: ${key}. Only UI preferences are allowed.`);
      return false;
    }
    
    try {
      localStorage.removeItem(STORAGE_PREFIX + key);
      return true;
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
      return false;
    }
  },

  // Clear all application data from localStorage
  clearAll: () => {
    try {
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(STORAGE_PREFIX)) {
          keysToRemove.push(key);
        }
      }
      
      keysToRemove.forEach(key => localStorage.removeItem(key));
      
      // Also clear any legacy keys that might exist
      const legacyKeys = [
        'session_id',
        'chat_session_id', 
        'lastAccessedChats',
        'currentChatId',
        'chats'
      ];
      
      legacyKeys.forEach(key => {
        localStorage.removeItem(key);
        localStorage.removeItem(STORAGE_PREFIX + key);
      });
      
      return true;
    } catch (error) {
      console.error('Error clearing localStorage:', error);
      return false;
    }
  },

  // Get all stored preferences
  getAllPreferences: () => {
    const preferences = {};
    ALLOWED_KEYS.forEach(key => {
      const value = storage.get(key);
      if (value !== null) {
        preferences[key] = value;
      }
    });
    return preferences;
  }
};

export default storage;
