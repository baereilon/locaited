import React from 'react';
import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Link,
  Stack,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  LocationOn as LocationIcon,
  AccessTime as TimeIcon,
  OpenInNew as OpenInNewIcon,
  CalendarMonth as CalendarIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

const EventCard = ({ event }) => {
  const formatDateTime = () => {
    const formatDate = (dateStr) => {
      if (!dateStr || dateStr === 'null') return null;
      try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        return date.toLocaleDateString('en-US', { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric',
          year: 'numeric'
        });
      } catch {
        return dateStr;
      }
    };

    const dateDisplay = formatDate(event.date);
    
    if (!dateDisplay) {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Date Required"
          color="error"
          variant="outlined"
          size="small"
          sx={{ borderRadius: 2 }}
        />
      );
    }
    
    if (event.time && event.time !== 'null') {
      return (
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip
            icon={<CalendarIcon />}
            label={dateDisplay}
            variant="filled"
            sx={{ 
              bgcolor: 'primary.light',
              color: 'primary.dark',
              fontWeight: 600,
              borderRadius: 2,
            }}
          />
          <Chip
            icon={<TimeIcon />}
            label={event.time}
            variant="outlined"
            sx={{ borderRadius: 2 }}
          />
        </Stack>
      );
    }
    
    return (
      <Chip
        icon={<CalendarIcon />}
        label={dateDisplay}
        variant="filled"
        sx={{ 
          bgcolor: 'primary.light',
          color: 'primary.dark',
          fontWeight: 600,
          borderRadius: 2,
        }}
      />
    );
  };

  // Calculate score color
  const getScoreColor = (score) => {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#FF9800';
    if (score >= 40) return '#2196F3';
    return '#9E9E9E';
  };

  const scoreValue = Math.round(event.score || 0);
  const scoreColor = getScoreColor(scoreValue);

  return (
    <Card 
      sx={{ 
        mb: 3,
        overflow: 'visible',
        position: 'relative',
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      {/* Photo Score Badge - Circular, positioned top-right */}
      <Box
        sx={{
          position: 'absolute',
          top: -10,
          right: 20,
          zIndex: 1,
        }}
      >
        <Avatar
          sx={{
            width: 60,
            height: 60,
            bgcolor: 'background.paper',
            border: '3px solid',
            borderColor: scoreColor,
            color: scoreColor,
            fontWeight: 700,
            fontSize: '1.25rem',
            boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)',
          }}
        >
          {scoreValue}
        </Avatar>
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            textAlign: 'center',
            mt: 0.5,
            color: 'text.secondary',
            fontWeight: 500,
          }}
        >
          Photo Score
        </Typography>
      </Box>

      <CardContent sx={{ p: 3, pb: 2 }}>
        <Stack spacing={2.5}>
          {/* Event Title - Bold and prominent */}
          <Box sx={{ pr: 8 }}>
            <Typography 
              variant="h5" 
              component="h3" 
              sx={{ 
                fontWeight: 700,
                color: 'text.primary',
                lineHeight: 1.3,
                mb: 1,
              }}
            >
              {event.title || 'Untitled Event'}
            </Typography>

            {/* Date/Time Section */}
            <Box sx={{ mt: 2 }}>
              {formatDateTime()}
            </Box>
          </Box>

          {/* Location with better styling */}
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              bgcolor: 'grey.50',
              borderRadius: 2,
              p: 1.5,
            }}
          >
            <LocationIcon sx={{ color: 'primary.main', mr: 1.5 }} />
            {event.location ? (
              <Box sx={{ flex: 1 }}>
                <Link 
                  href={`https://maps.google.com/?q=${encodeURIComponent(event.location)}`}
                  target="_blank"
                  rel="noopener"
                  underline="hover"
                  sx={{
                    color: 'text.primary',
                    fontWeight: 500,
                    '&:hover': {
                      color: 'primary.main',
                    },
                  }}
                >
                  {event.location}
                </Link>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Location to be determined
              </Typography>
            )}
          </Box>

          {/* Description with better typography */}
          {(event.description || event.summary) && (
            <Box 
              sx={{ 
                borderLeft: '3px solid',
                borderColor: 'primary.light',
                pl: 2,
                py: 0.5,
              }}
            >
              <Typography 
                variant="body1" 
                color="text.secondary"
                sx={{ lineHeight: 1.7 }}
              >
                {(event.description || event.summary).length > 200 
                  ? `${(event.description || event.summary).substring(0, 200)}...` 
                  : (event.description || event.summary)}
              </Typography>
            </Box>
          )}

          {/* Organizer info if available */}
          {event.organizer && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Organized by
              </Typography>
              <Chip
                label={event.organizer}
                size="small"
                variant="outlined"
                sx={{ borderRadius: 2 }}
              />
            </Box>
          )}

          {/* Why Recommended - Enhanced visual */}
          {event.rationale && (
            <Box 
              sx={{ 
                bgcolor: 'secondary.light',
                borderRadius: 2,
                p: 2,
              }}
            >
              <Typography 
                variant="body2" 
                sx={{ 
                  fontStyle: 'italic',
                  color: 'text.primary',
                  fontWeight: 500,
                }}
              >
                💡 {event.rationale}
              </Typography>
            </Box>
          )}

          {/* Source Link - Better positioned */}
          {event.url && (
            <Box 
              sx={{ 
                display: 'flex', 
                justifyContent: 'flex-end',
                pt: 1,
                borderTop: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Tooltip title="View source">
                <IconButton
                  href={event.url}
                  target="_blank"
                  rel="noopener"
                  size="small"
                  sx={{
                    color: 'primary.main',
                    '&:hover': {
                      bgcolor: 'primary.light',
                    },
                  }}
                >
                  <OpenInNewIcon />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

EventCard.propTypes = {
  event: PropTypes.shape({
    title: PropTypes.string,
    date: PropTypes.string,
    time: PropTypes.string,
    location: PropTypes.string,
    summary: PropTypes.string,
    description: PropTypes.string,
    score: PropTypes.number,
    rationale: PropTypes.string,
    url: PropTypes.string,
    organizer: PropTypes.string,
  }).isRequired,
};

export default EventCard;