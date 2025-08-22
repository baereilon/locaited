import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import App from '../../App';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api');

describe('Results Display Integration - Simplified', () => {
  const theme = createTheme();
  
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    
    // Mock successful health check by default
    api.checkHealth = vi.fn().mockResolvedValue(true);
  });

  it('renders the app without crashing', () => {
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Verify key elements are present
    expect(screen.getByText(/LocAIted/)).toBeInTheDocument();
    expect(screen.getByText(/Event Discovery/)).toBeInTheDocument();
  });

  it('shows the discovery form', () => {
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Check form is visible
    expect(screen.getByLabelText(/What events are you looking for/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Discover Events/i })).toBeInTheDocument();
  });

  it('calls API when form is submitted', async () => {
    // Mock API response
    api.discoverEvents = vi.fn().mockResolvedValue({
      events: [],
      total_cost: 0,
      cache_hits: 0,
      status: 'success',
      message: 'No events found',
    });
    
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    );
    
    // Fill minimum required fields
    const queryInput = screen.getByLabelText(/What events are you looking for/i);
    fireEvent.change(queryInput, { target: { value: 'test query for events' } });
    
    // Select an interest
    const protestChip = screen.getByText('Protests');
    fireEvent.click(protestChip);
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Discover Events/i });
    fireEvent.click(submitButton);
    
    // Verify API was called
    await waitFor(() => {
      expect(api.discoverEvents).toHaveBeenCalled();
    });
  });
});