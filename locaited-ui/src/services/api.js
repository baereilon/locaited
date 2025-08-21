import axios from 'axios';
import { API_BASE_URL } from '../config/constants';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMessage = error.response?.data?.detail || 
                        error.message || 
                        'An unexpected error occurred';
    
    // Create a more user-friendly error
    const enhancedError = new Error(errorMessage);
    enhancedError.status = error.response?.status;
    enhancedError.originalError = error;
    
    return Promise.reject(enhancedError);
  }
);

/**
 * Submit event discovery request with profile and query
 * @param {Object} requestData - The discovery request data
 * @param {AbortSignal} signal - Optional abort signal for cancellation
 * @returns {Promise<Object>} Workflow response with events and metrics
 */
export const discoverEvents = async (requestData, signal = null) => {
  try {
    const response = await apiClient.post('/workflow/discover', requestData, {
      signal: signal,
      timeout: 300000, // 5 minute timeout
    });
    return response.data;
  } catch (error) {
    // Check if request was cancelled
    if (axios.isCancel(error)) {
      throw {
        message: 'Request cancelled by user',
        isCancelled: true,
      };
    }
    // Re-throw with additional context
    throw {
      message: error.message,
      status: error.status,
      isNetworkError: !error.status,
    };
  }
};

/**
 * Get cache statistics
 * @returns {Promise<Object>} Cache stats
 */
export const getCacheStats = async () => {
  try {
    const response = await apiClient.get('/cache/stats');
    return response.data;
  } catch (error) {
    // Non-critical, return empty stats on error
    console.error('Failed to fetch cache stats:', error);
    return { search_entries: 0, extract_entries: 0, llm_entries: 0 };
  }
};

/**
 * Health check for API
 * @returns {Promise<boolean>} True if API is healthy
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/');
    return response.data?.status === 'healthy';
  } catch (error) {
    return false;
  }
};

export default {
  discoverEvents,
  getCacheStats,
  checkHealth,
};