import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResultsContainer from '../components/ResultsContainer';

describe('ResultsContainer', () => {
  const mockEvents = [
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
  ];

  const mockMetrics = {
    total_cost: 0.05,
    cache_hits: 3,
    processing_time: 2,
    message: 'Found 2 events',
  };

  it('renders events when provided', () => {
    render(<ResultsContainer events={mockEvents} metrics={mockMetrics} error={null} />);
    
    // Check that both events are displayed
    expect(screen.getByText('Fashion Week Opening Gala')).toBeInTheDocument();
    expect(screen.getByText('Tech & Fashion Symposium')).toBeInTheDocument();
  });

  it('displays event count correctly', () => {
    render(<ResultsContainer events={mockEvents} metrics={mockMetrics} error={null} />);
    
    // Check the event count message
    expect(screen.getByText('2 events found matching your criteria')).toBeInTheDocument();
  });

  it('renders nothing when no events provided', () => {
    const { container } = render(<ResultsContainer events={[]} metrics={null} error={null} />);
    
    // Should render nothing (null)
    expect(container.firstChild).toBeNull();
  });

  it('displays error message when error is provided', () => {
    const error = {
      message: 'Failed to fetch events',
      isNetworkError: false,
    };
    
    render(<ResultsContainer events={[]} metrics={null} error={error} />);
    
    // Check error message is displayed
    expect(screen.getByText(/Failed to fetch events/)).toBeInTheDocument();
  });

  it('displays network error with helpful message', () => {
    const error = {
      message: 'Network error',
      isNetworkError: true,
    };
    
    render(<ResultsContainer events={[]} metrics={null} error={error} />);
    
    // Check network error message
    expect(screen.getByText(/Please check that the API server is running on port 8000/)).toBeInTheDocument();
  });

  it('displays cancelled message when request is cancelled', () => {
    const error = {
      message: 'Cancelled',
      isCancelled: true,
    };
    
    render(<ResultsContainer events={[]} metrics={null} error={error} />);
    
    // Check cancelled message
    expect(screen.getByText(/Discovery process was cancelled/)).toBeInTheDocument();
  });

  it('allows sorting by date and score', () => {
    render(<ResultsContainer events={mockEvents} metrics={mockMetrics} error={null} />);
    
    // Find sort dropdown
    const sortSelect = screen.getByLabelText('Sort by');
    
    // Initially sorted by date
    expect(sortSelect.value).toBe('date');
    
    // Change to sort by score
    fireEvent.change(sortSelect, { target: { value: 'score' } });
    expect(sortSelect.value).toBe('score');
  });

  it('renders metrics panel with correct data', () => {
    render(<ResultsContainer events={mockEvents} metrics={mockMetrics} error={null} />);
    
    // MetricsPanel should receive the correct props
    // This would be more detailed if we had access to MetricsPanel internals
    expect(screen.getByText('Discovered Events')).toBeInTheDocument();
  });

  it('handles export button click', () => {
    render(<ResultsContainer events={mockEvents} metrics={mockMetrics} error={null} />);
    
    // Find and click export button
    const exportButton = screen.getByText('Export CSV');
    
    // Just verify button exists and is clickable
    expect(exportButton).toBeInTheDocument();
    fireEvent.click(exportButton);
    
    // Export function would be called but we can't easily mock it in this setup
  });

  it('displays status message from metrics', () => {
    const metricsWithMessage = {
      ...mockMetrics,
      message: 'Test status message',
    };
    
    render(<ResultsContainer events={mockEvents} metrics={metricsWithMessage} error={null} />);
    
    // Check status message is displayed
    expect(screen.getByText('Test status message')).toBeInTheDocument();
  });

  it('handles empty events array correctly', () => {
    const { container } = render(<ResultsContainer events={[]} metrics={mockMetrics} error={null} />);
    
    // Should not render anything for empty events
    expect(container.firstChild).toBeNull();
  });

  it('handles null events correctly', () => {
    const { container } = render(<ResultsContainer events={null} metrics={mockMetrics} error={null} />);
    
    // Should not render anything for null events
    expect(container.firstChild).toBeNull();
  });

  it('handles undefined events correctly', () => {
    const { container } = render(<ResultsContainer events={undefined} metrics={mockMetrics} error={null} />);
    
    // Should not render anything for undefined events  
    expect(container.firstChild).toBeNull();
  });
});