import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import App from '../../App';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api');

describe('Results Display Integration', () => {
  const theme = createTheme();
  
  const mockSuccessResponse = {
    events: [
      {
        title: 'Fashion Week Opening Gala',
        location: 'Bryant Park, NYC',
        time: '2025-08-25 18:00',
        url: 'https://example.com/fashion-week',
        access_req: 'public_only',
        summary: 'Annual fashion week opening ceremony',
        score: 95,
        rationale: 'Highly relevant fashion event',
      },
      {
        title: 'Tech & Fashion Symposium',
        location: 'Museum of Modern Art, NYC',
        time: '2025-08-26 14:00',
        url: 'https://example.com/tech-fashion',
        access_req: 'public_only',
        summary: 'Exploring technology and fashion',
        score: 88,
        rationale: 'Combines both interests',
      },
    ],
    total_cost: 0.05,
    cache_hits: 3,
    status: 'success',
    message: 'Found 2 events',
  };

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    
    // Mock successful health check
    api.checkHealth = vi.fn().mockResolvedValue(true);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('displays results after successful API call', async () => {
    // Mock successful API response
    api.discoverEvents = vi.fn().mockResolvedValue(mockSuccessResponse);
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Fill in the form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'fashion events' } });
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Fashion Week Opening Gala')).toBeInTheDocument();
    }, { timeout: 5000 });
    
    // Verify both events are displayed
    expect(screen.getByText('Tech & Fashion Symposium')).toBeInTheDocument();
    
    // Verify event details are shown
    expect(screen.getByText(/Annual fashion week opening ceremony/)).toBeInTheDocument();
    expect(screen.getByText(/Exploring technology and fashion/)).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    // Mock API error
    api.discoverEvents = vi.fn().mockRejectedValue({
      message: 'API Error: Failed to fetch events',
      isNetworkError: false,
    });
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Fill and submit form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch events/)).toBeInTheDocument();
    });
  });

  it('displays network error with helpful message', async () => {
    // Mock network error
    api.discoverEvents = vi.fn().mockRejectedValue({
      message: 'Network request failed',
      isNetworkError: true,
    });
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Fill and submit form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Wait for network error message
    await waitFor(() => {
      expect(screen.getByText(/Please check that the API server is running/)).toBeInTheDocument();
    });
  });

  it('shows loading state during API call', async () => {
    // Mock delayed API response
    let resolvePromise;
    const delayedPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    api.discoverEvents = vi.fn().mockReturnValue(delayedPromise);
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Submit form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Check loading state (StatusIndicator should be visible)
    await waitFor(() => {
      expect(screen.getByText(/Analyzing your request/)).toBeInTheDocument();
    });
    
    // Resolve the promise
    resolvePromise(mockSuccessResponse);
    
    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Fashion Week Opening Gala')).toBeInTheDocument();
    });
  });

  it('handles empty results gracefully', async () => {
    // Mock empty results
    api.discoverEvents = vi.fn().mockResolvedValue({
      events: [],
      total_cost: 0.01,
      cache_hits: 0,
      status: 'success',
      message: 'No events found',
    });
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Submit form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'obscure query' } });
    
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Wait for completion
    await waitFor(() => {
      expect(api.discoverEvents).toHaveBeenCalled();
    });
    
    // No events should be displayed
    expect(screen.queryByText('Discovered Events')).not.toBeInTheDocument();
  });

  it('allows cancellation of ongoing request', async () => {
    // Mock long-running API call
    let abortSignal;
    api.discoverEvents = vi.fn().mockImplementation((data, signal) => {
      abortSignal = signal;
      return new Promise(() => {}); // Never resolves
    });
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Submit form
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Wait for loading state
    await waitFor(() => {
      expect(screen.getByText(/Analyzing your request/)).toBeInTheDocument();
    });
    
    // Click cancel button
    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);
    
    // Check that abort was called
    expect(abortSignal?.aborted).toBe(true);
    
    // Check for cancelled message
    await waitFor(() => {
      expect(screen.getByText(/Discovery cancelled/)).toBeInTheDocument();
    });
  });
});