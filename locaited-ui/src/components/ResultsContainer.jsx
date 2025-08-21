import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  Stack,
  Alert,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
import EventCard from './EventCard';
import MetricsPanel from './MetricsPanel';
import { exportToCSV } from '../utils/csvExport';

const ResultsContainer = ({ events, metrics, error }) => {
  const [sortBy, setSortBy] = useState('date');

  const sortedEvents = useMemo(() => {
    if (!events || events.length === 0) return [];
    
    const sorted = [...events];
    switch (sortBy) {
      case 'score':
        return sorted.sort((a, b) => (b.score || 0) - (a.score || 0));
      case 'date':
      default:
        return sorted.sort((a, b) => {
          // Parse dates for proper sorting
          const dateA = new Date(a.date || a.time || 0);
          const dateB = new Date(b.date || b.time || 0);
          return dateA - dateB;
        });
    }
  }, [events, sortBy]);

  const handleExport = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    exportToCSV(sortedEvents, `locaited_events_${timestamp}.csv`);
  };

  // Error state
  if (error) {
    // Show info alert for cancelled requests
    if (error.isCancelled) {
      return (
        <Alert severity="info" sx={{ my: 2 }}>
          <Typography variant="body1">
            Discovery process was cancelled. Try again when you're ready.
          </Typography>
        </Alert>
      );
    }
    
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        <Typography variant="body1" gutterBottom>
          <strong>Error:</strong> {error.message || 'Failed to discover events'}
        </Typography>
        {error.isNetworkError && (
          <Typography variant="body2">
            Please check that the API server is running on port 8000.
          </Typography>
        )}
      </Alert>
    );
  }

  // Empty state
  if (!events || events.length === 0) {
    return null;
  }

  return (
    <Box sx={{ my: 4 }}>
      {/* Metrics Panel */}
      <MetricsPanel 
        metrics={{
          eventCount: events.length,
          totalCost: metrics?.total_cost,
          cacheHits: metrics?.cache_hits,
          processingTime: metrics?.processing_time,
        }}
      />

      {/* Controls */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography 
            variant="h5"
            sx={{ 
              fontWeight: 700,
              color: 'text.primary',
              mb: 0.5,
            }}
          >
            Discovered Events
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {events.length} events found matching your criteria
          </Typography>
        </Box>
        
        <Stack direction="row" spacing={2}>
          <FormControl 
            size="small" 
            sx={{ 
              minWidth: 120,
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          >
            <InputLabel>Sort by</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort by"
            >
              <MenuItem value="date">Date</MenuItem>
              <MenuItem value="score">Score</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            sx={{
              borderRadius: 2,
              fontWeight: 500,
            }}
          >
            Export CSV
          </Button>
        </Stack>
      </Stack>

      {/* Event Cards */}
      <Box>
        {sortedEvents.map((event, index) => (
          <EventCard key={index} event={event} />
        ))}
      </Box>

      {/* Status message if applicable */}
      {metrics?.message && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {metrics.message}
        </Alert>
      )}
    </Box>
  );
};

ResultsContainer.propTypes = {
  events: PropTypes.arrayOf(PropTypes.object),
  metrics: PropTypes.shape({
    total_cost: PropTypes.number,
    cache_hits: PropTypes.number,
    processing_time: PropTypes.number,
    message: PropTypes.string,
  }),
  error: PropTypes.shape({
    message: PropTypes.string,
    isNetworkError: PropTypes.bool,
  }),
};

ResultsContainer.defaultProps = {
  events: [],
  metrics: null,
  error: null,
};

export default ResultsContainer;