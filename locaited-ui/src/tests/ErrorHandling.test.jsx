import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EventCard from '../components/EventCard';
import ResultsContainer from '../components/ResultsContainer';

describe('Error Handling and Edge Cases', () => {
  
  describe('EventCard Error Handling', () => {
    it('handles missing event data gracefully', () => {
      const incompleteEvent = {
        title: 'Test Event',
        // Missing other fields
      };
      
      render(<EventCard event={incompleteEvent} />);
      
      // Should still render the title
      expect(screen.getByText('Test Event')).toBeInTheDocument();
      
      // Should show date required when no date
      expect(screen.getByText('Date Required')).toBeInTheDocument();
    });
    
    it('handles null time gracefully', () => {
      const eventWithNullTime = {
        title: 'Test Event',
        location: 'NYC',
        date: '2025-08-25',
        time: null,
        url: 'https://example.com',
        access_req: 'public',
        summary: 'Test summary',
        score: 75,
      };
      
      render(<EventCard event={eventWithNullTime} />);
      
      // Should still display the date
      expect(screen.getByText(/Aug/)).toBeInTheDocument();
    });
    
    it('handles invalid score values', () => {
      const eventWithInvalidScore = {
        title: 'Test Event',
        location: 'NYC',
        date: '2025-08-25',
        time: '18:00',
        url: 'https://example.com',
        access_req: 'public',
        summary: 'Test summary',
        score: 150, // Invalid score > 100
      };
      
      render(<EventCard event={eventWithInvalidScore} />);
      
      // Should still render without crashing
      expect(screen.getByText('Test Event')).toBeInTheDocument();
      expect(screen.getByText('Photo Score')).toBeInTheDocument();
    });
  });
  
  describe('ResultsContainer Error Scenarios', () => {
    it('handles network timeout error', () => {
      const timeoutError = {
        message: 'Request timeout',
        isNetworkError: true,
        code: 'ECONNABORTED',
      };
      
      render(<ResultsContainer events={[]} metrics={null} error={timeoutError} />);
      
      // Should show timeout-specific message
      expect(screen.getByText(/Request timeout/i)).toBeInTheDocument();
    });
    
    it('handles server error (500)', () => {
      const serverError = {
        message: 'Internal Server Error',
        status: 500,
      };
      
      render(<ResultsContainer events={[]} metrics={null} error={serverError} />);
      
      // Should show server error message
      expect(screen.getByText(/Internal Server Error/)).toBeInTheDocument();
    });
  });
  
  describe('Boundary Conditions', () => {
    it('handles exactly 0 events', () => {
      const { container } = render(
        <ResultsContainer events={[]} metrics={null} error={null} />
      );
      
      // Should render nothing
      expect(container.firstChild).toBeNull();
    });
    
    it('handles exactly 1 event', () => {
      const singleEvent = [{
        title: 'Single Event',
        location: 'NYC',
        date: '2025-08-25',
        time: '18:00',
        url: 'https://example.com',
        access_req: 'public',
        summary: 'Summary',
        score: 80,
      }];
      
      const metrics = {
        total_cost: 0.01,
        cache_hits: 1,
      };
      
      render(<ResultsContainer events={singleEvent} metrics={metrics} error={null} />);
      
      // Should display the single event
      expect(screen.getByText('Single Event')).toBeInTheDocument();
      expect(screen.getByText('1 events found matching your criteria')).toBeInTheDocument();
    });
  });
});