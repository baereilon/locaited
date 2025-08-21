import { describe, it, expect, vi } from 'vitest';

// Simple test without mocking to verify the API functions exist
describe('API Service - Simple Tests', () => {
  it('API functions are exported', async () => {
    const api = await import('../services/api');
    
    expect(api.discoverEvents).toBeDefined();
    expect(typeof api.discoverEvents).toBe('function');
    
    expect(api.checkHealth).toBeDefined();
    expect(typeof api.checkHealth).toBe('function');
    
    expect(api.getCacheStats).toBeDefined();
    expect(typeof api.getCacheStats).toBe('function');
  });
  
  it('API base URL is configured', async () => {
    const constants = await import('../config/constants');
    expect(constants.API_BASE_URL).toBeDefined();
    expect(constants.API_BASE_URL).toContain('http');
  });
});