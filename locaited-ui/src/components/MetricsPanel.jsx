import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Collapse,
  Paper,
  Typography,
  Grid,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

const MetricsPanel = ({ metrics }) => {
  const [expanded, setExpanded] = useState(false);

  if (!metrics) {
    return null;
  }

  return (
    <Paper elevation={1} sx={{ p: 2, my: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body1">
          <strong>{metrics.eventCount || 0}</strong> events found
        </Typography>
        <Button
          size="small"
          onClick={() => setExpanded(!expanded)}
          endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        >
          {expanded ? 'Hide' : 'Show'} Metrics
        </Button>
      </Box>
      
      <Collapse in={expanded}>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={4}>
            <Typography variant="body2" color="text.secondary">
              Total Cost
            </Typography>
            <Typography variant="h6">
              ${metrics.totalCost?.toFixed(4) || '0.0000'}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" color="text.secondary">
              Cache Hits
            </Typography>
            <Typography variant="h6">
              {metrics.cacheHits || 0}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" color="text.secondary">
              Processing Time
            </Typography>
            <Typography variant="h6">
              {metrics.processingTime ? `${metrics.processingTime}s` : 'N/A'}
            </Typography>
          </Grid>
        </Grid>
      </Collapse>
    </Paper>
  );
};

MetricsPanel.propTypes = {
  metrics: PropTypes.shape({
    eventCount: PropTypes.number,
    totalCost: PropTypes.number,
    cacheHits: PropTypes.number,
    processingTime: PropTypes.number,
  }),
};

export default MetricsPanel;