import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

// Mock axios entirely
vi.mock('axios');

describe('API Service', () => {
  let discoverEvents, checkHealth;
  let mockPost, mockGet;

  beforeEach(async () => {
    // Clear all mocks
    vi.clearAllMocks();
    
    // Create mock functions
    mockPost = vi.fn();
    mockGet = vi.fn();
    
    // Setup axios mock
    axios.create = vi.fn(() => ({
      post: mockPost,
      get: mockGet,
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn((success, error) => {
          // Store the error handler for testing
          axios.create.errorHandler = error;
        }) }
      }
    }));
    
    axios.isCancel = vi.fn(() => false);
    
    // Import the module fresh for each test
    const api = await import('../services/api');
    discoverEvents = api.discoverEvents;
    checkHealth = api.checkHealth;
  });

  afterEach(() => {
    vi.resetModules();
  });

  describe('discoverEvents', () => {
    it('sends correct request payload', async () => {
      const mockResponse = {
        data: {
          events: [],
          total_cost: 0.01,
          cache_hits: 2,
          status: 'success'
        }
      };
      
      mockPost.mockResolvedValueOnce(mockResponse);
      
      const requestData = {
        location: 'NYC',
        interest_areas: ['protests'],
        query: 'test query',
        days_ahead: 7
      };
      
      const result = await discoverEvents(requestData);
      
      expect(mockPost).toHaveBeenCalledWith('/workflow/discover', requestData, expect.objectContaining({
        signal: null,
        timeout: 300000
      }));
      expect(result).toEqual(mockResponse.data);
    });

    it('handles API errors properly', async () => {
      const mockError = new Error('API Error');
      mockError.response = { 
        status: 500,
        data: { detail: 'Server error' }
      };
      
      mockPost.mockRejectedValueOnce(mockError);
      
      try {
        await discoverEvents({});
        // Should not reach here
        expect.fail('Expected error to be thrown');
      } catch (error) {
        expect(error.status).toBe(500);
        expect(error.message).toBe('Server error');
      }
    });

    it('identifies network errors', async () => {
      const networkError = new Error('Network Error');
      // No response means network error
      
      mockPost.mockRejectedValueOnce(networkError);
      
      try {
        await discoverEvents({});
      } catch (error) {
        expect(error.isNetworkError).toBe(true);
      }
    });

    it('handles cancelled requests', async () => {
      const cancelError = new Error('Request cancelled');
      axios.isCancel = vi.fn(() => true);
      
      mockPost.mockRejectedValueOnce(cancelError);
      
      try {
        await discoverEvents({});
      } catch (error) {
        expect(error.isCancelled).toBe(true);
        expect(error.message).toBe('Request cancelled by user');
      }
    });
  });

  describe('checkHealth', () => {
    it('returns true when API is healthy', async () => {
      mockGet.mockResolvedValueOnce({
        data: { status: 'healthy' }
      });
      
      const result = await checkHealth();
      expect(result).toBe(true);
    });

    it('returns false when API is down', async () => {
      mockGet.mockRejectedValueOnce(new Error('Connection refused'));
      
      const result = await checkHealth();
      expect(result).toBe(false);
    });
  });
});