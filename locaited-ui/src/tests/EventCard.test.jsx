import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EventCard from '../components/EventCard';

describe('EventCard', () => {
  const mockEvent = {
    title: 'Climate Protest at City Hall',
    date: '2024-08-25',
    time: '2:00 PM',
    location: 'City Hall, NYC',
    description: 'Large climate protest expected with hundreds of participants',
    score: 85,
    rationale: 'High visual impact, timely issue',
    url: 'https://example.com/event',
    organizer: 'Climate Action NYC'
  };

  it('renders all event information', () => {
    render(<EventCard event={mockEvent} />);
    
    expect(screen.getByText(mockEvent.title)).toBeInTheDocument();
    expect(screen.getByText(mockEvent.location)).toBeInTheDocument();
    expect(screen.getByText(/High visual impact/)).toBeInTheDocument();
  });

  it('displays date and time when both present', () => {
    render(<EventCard event={mockEvent} />);
    
    // Check for date display (will be formatted)
    expect(screen.getByText(/Aug/)).toBeInTheDocument();
    // Check for time
    expect(screen.getByText(mockEvent.time)).toBeInTheDocument();
  });

  it('displays only date when time is missing', () => {
    const eventWithoutTime = { ...mockEvent, time: null };
    render(<EventCard event={eventWithoutTime} />);
    
    // Should still show date
    expect(screen.getByText(/Aug/)).toBeInTheDocument();
  });

  it('shows date required error when date is missing', () => {
    const eventWithoutDate = { ...mockEvent, date: null };
    render(<EventCard event={eventWithoutDate} />);
    
    expect(screen.getByText('Date Required')).toBeInTheDocument();
  });

  it('displays photo score badge', () => {
    render(<EventCard event={mockEvent} />);
    
    // Score is displayed in avatar badge
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Photo Score')).toBeInTheDocument();
  });

  it('truncates long descriptions', () => {
    const longDescription = 'A'.repeat(250);
    const eventWithLongDesc = { ...mockEvent, description: longDescription };
    
    render(<EventCard event={eventWithLongDesc} />);
    
    // Should truncate to 200 chars + ...
    const description = screen.getByText(/A{200}\.\.\.$/);
    expect(description).toBeInTheDocument();
  });

  it('handles missing fields gracefully', () => {
    const minimalEvent = {
      title: 'Test Event',
      date: '2024-08-25',
      location: 'Test Location',
      score: 50
    };
    
    render(<EventCard event={minimalEvent} />);
    
    // Should still render without crashing
    expect(screen.getByText('Test Event')).toBeInTheDocument();
    expect(screen.getByText('Test Location')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('shows organizer when available', () => {
    render(<EventCard event={mockEvent} />);
    
    expect(screen.getByText('Organized by')).toBeInTheDocument();
    expect(screen.getByText(mockEvent.organizer)).toBeInTheDocument();
  });

  it('displays rationale with emoji', () => {
    render(<EventCard event={mockEvent} />);
    
    // Check for lightbulb emoji and rationale text
    expect(screen.getByText(/💡.*High visual impact/)).toBeInTheDocument();
  });

  it('renders source link when URL is provided', () => {
    render(<EventCard event={mockEvent} />);
    
    // Look for the link icon button
    const linkButton = screen.getByRole('link', { name: /view source/i });
    expect(linkButton).toHaveAttribute('href', mockEvent.url);
  });
});