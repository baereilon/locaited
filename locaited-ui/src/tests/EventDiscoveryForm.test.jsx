import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EventDiscoveryForm from '../components/EventDiscoveryForm';

describe('EventDiscoveryForm', () => {
  const mockSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all required fields', () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    // Check for form elements
    expect(screen.getByText('New York City')).toBeInTheDocument(); // Location select shows default value
    expect(screen.getByText(/interest areas/i)).toBeInTheDocument();
    expect(screen.getByText('Next 7 days')).toBeInTheDocument(); // Time window shows default
    expect(screen.getByLabelText(/what events are you looking for/i)).toBeInTheDocument();
  });

  it('validates interest areas selection', async () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    // Try to submit without selecting interests
    const submitButton = screen.getByRole('button', { name: /discover events/i });
    fireEvent.click(submitButton);
    
    // Should show error
    await waitFor(() => {
      expect(screen.getByText(/please select at least one interest area/i)).toBeInTheDocument();
    });
    
    // Should not call submit
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('validates query length', async () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    const queryField = screen.getByLabelText(/what events are you looking for/i);
    
    // Too short
    await userEvent.type(queryField, 'short');
    fireEvent.click(screen.getByRole('button', { name: /discover events/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/minimum 10 characters/i)).toBeInTheDocument();
    });
  });

  it('shows custom location field when selected', async () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    // Custom location field should not be visible initially
    expect(screen.queryByLabelText(/custom location/i)).not.toBeInTheDocument();
    
    // Click on the location select (find by current value)
    const locationSelect = screen.getByText('New York City');  // Default value
    fireEvent.mouseDown(locationSelect);
    
    const customOption = await screen.findByText('Custom Location');
    fireEvent.click(customOption);
    
    // Custom location field should appear
    expect(screen.getByLabelText(/custom location/i)).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    // Select an interest
    const protestChip = screen.getByText('Protests');
    fireEvent.click(protestChip);
    
    // Enter query
    const queryField = screen.getByLabelText(/what events are you looking for/i);
    await userEvent.type(queryField, 'Looking for interesting protests and rallies');
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /discover events/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          location: 'NYC',
          interest_areas: ['protests'],
          query: 'Looking for interesting protests and rallies',
          days_ahead: 7
        })
      );
    });
  });

  it('clears form when clear button is clicked', async () => {
    render(<EventDiscoveryForm onSubmit={mockSubmit} />);
    
    // Fill in some data
    const protestChip = screen.getByText('Protests');
    fireEvent.click(protestChip);
    
    const queryField = screen.getByLabelText(/what events are you looking for/i);
    await userEvent.type(queryField, 'Test query');
    
    // Clear form
    const clearButton = screen.getByRole('button', { name: /clear form/i });
    fireEvent.click(clearButton);
    
    // Check fields are reset
    expect(queryField.value).toBe('');
    expect(protestChip).not.toHaveClass('MuiChip-colorPrimary');
  });
});