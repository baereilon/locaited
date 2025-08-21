import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  Collapse,
  Grid,
  Card,
  CardContent,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  DataObject as DataIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';

const AgentOutput = ({ agent, data }) => {
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (!agent || !data) {
    return (
      <Box sx={{ 
        p: 4, 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <Box sx={{ textAlign: 'center' }}>
          <Box sx={{ 
            width: 64, 
            height: 64, 
            bgcolor: 'grey.100', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            mx: 'auto',
            mb: 2
          }}>
            <DataIcon sx={{ fontSize: 32, color: 'grey.400' }} />
          </Box>
          <Typography variant="h6" gutterBottom>
            Waiting for Agent
          </Typography>
          <Typography color="text.secondary">
            The debug session will show agent output here
          </Typography>
        </Box>
      </Box>
    );
  }

  const renderEditorOutput = (data) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert severity="info" sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          Profile Created
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2">
              <strong>Location:</strong> {data.profile?.location}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2">
              <strong>Timeframe:</strong> {data.profile?.timeframe}
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="body2">
              <strong>Interests:</strong> {data.profile?.interests?.join(', ')}
            </Typography>
          </Grid>
        </Grid>
      </Alert>
      
      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          Guidance for Researcher
        </Typography>
        <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
          "{data.guidance}"
        </Typography>
      </Paper>
    </Box>
  );

  const renderResearcherOutput = (data) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert severity="success">
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          {data.summary}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>Total Leads:</strong> {data.total_leads}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>Lead Types:</strong> {Object.keys(data.lead_types || {}).length}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>Showing:</strong> {data.preview?.length || 0}
            </Typography>
          </Grid>
        </Grid>
      </Alert>

      <Box>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          Generated Leads (Preview)
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {(expandedSections.all_leads ? data.raw_data?.leads || [] : data.preview || []).map((lead, index) => (
            <Card key={index} variant="outlined">
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {expandedSections.all_leads ? `${index + 1}. ${lead.description}` : `${lead.number}. ${lead.description}`}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Type: <strong>{lead.type}</strong> | Keywords: {lead.keywords?.join(', ')}
                </Typography>
                {lead.date && lead.date !== "No date" && (
                  <Typography variant="caption" color="primary.main" sx={{ mt: 0.5, display: 'block', fontWeight: 500 }}>
                    📅 {lead.date} {lead.time && `at ${lead.time}`}
                  </Typography>
                )}
                {lead.venue && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    📍 {lead.venue}
                  </Typography>
                )}
                {lead.source_url && (
                  <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                    🔗 <a href={lead.source_url} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
                      Source URL
                    </a>
                  </Typography>
                )}
                {expandedSections.all_leads && lead.search_query && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Search Query: {lead.search_query}
                  </Typography>
                )}
                {expandedSections.all_leads && lead.verification_note && (
                  <Typography variant="caption" color="success.main" sx={{ mt: 0.5, display: 'block' }}>
                    ✓ {lead.verification_note}
                  </Typography>
                )}
              </CardContent>
            </Card>
          ))}
          
          {data.show_all && (
            <Button
              onClick={() => toggleSection('all_leads')}
              size="small"
              color="primary"
            >
              {expandedSections.all_leads ? 'Show less' : `Show all ${data.total_leads} leads`}
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );

  const renderFactCheckerOutput = (data) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert severity="info" sx={{ bgcolor: 'secondary.light' }}>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          {data.summary}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>Searches:</strong> {data.total_searches}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>With Results:</strong> {data.searches_with_results}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2">
              <strong>Total Results:</strong> {data.total_results}
            </Typography>
          </Grid>
        </Grid>
      </Alert>

      <Box>
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          Search Results
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {data.search_details?.map((search, index) => (
            <Card key={index} variant="outlined">
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {search.description}
                  </Typography>
                  <Chip
                    label={search.status}
                    size="small"
                    color={search.results_found > 0 ? 'success' : 'error'}
                    variant="outlined"
                  />
                </Box>
                {search.results_found > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Results: {search.results_found}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Sources: {search.top_sources?.join(', ')}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>
    </Box>
  );

  const renderPublisherOutput = (data) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert
        severity={data.gate_decision === 'APPROVE' ? 'success' : 'warning'}
        sx={{
          bgcolor: data.gate_decision === 'APPROVE' ? 'success.light' : 'warning.light'
        }}
      >
        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
          {data.summary}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2">
              <strong>Total Events:</strong> {data.total_events}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2">
                <strong>Decision:</strong>
              </Typography>
              <Chip
                label={data.gate_decision}
                size="small"
                color={data.gate_decision === 'APPROVE' ? 'success' : 'warning'}
                variant="filled"
              />
            </Box>
          </Grid>
        </Grid>
        
        {data.quality_metrics && (
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={4}>
              <Typography variant="caption">With Time: {data.quality_metrics.with_time}</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption">With Description: {data.quality_metrics.with_description}</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption">With URL: {data.quality_metrics.with_url}</Typography>
            </Grid>
          </Grid>
        )}
      </Alert>

      {data.gate_decision === 'RETRY' && data.feedback && (
        <Alert severity="warning" sx={{ bgcolor: 'warning.light' }}>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
            Retry Feedback
          </Typography>
          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
            "{data.feedback}"
          </Typography>
        </Alert>
      )}

      {data.events_preview && data.events_preview.length > 0 && (
        <Box>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
            Extracted Events (Preview)
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {data.events_preview.map((event, index) => (
              <Card key={index} variant="outlined">
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {event.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    {event.date} {event.time && `at ${event.time}`} | {event.location}
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label={`Score: ${event.score}`} size="small" variant="outlined" />
                    <Chip 
                      label={`URL: ${event.has_url ? '✓' : '✗'}`} 
                      size="small" 
                      color={event.has_url ? 'success' : 'error'}
                      variant="outlined" 
                    />
                    <Chip 
                      label={`Description: ${event.has_description ? '✓' : '✗'}`} 
                      size="small" 
                      color={event.has_description ? 'success' : 'error'}
                      variant="outlined" 
                    />
                  </Box>
                </CardContent>
              </Card>
            ))}
            
            {data.show_all_events && (
              <Button
                onClick={() => toggleSection('all_events')}
                size="small"
                color="primary"
              >
                {expandedSections.all_events ? 'Show less' : `Show all ${data.total_events} events`}
              </Button>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );

  const renderOutput = () => {
    switch (agent) {
      case 'editor':
        return renderEditorOutput(data);
      case 'researcher':
        return renderResearcherOutput(data);
      case 'fact_checker':
        return renderFactCheckerOutput(data);
      case 'publisher':
        return renderPublisherOutput(data);
      default:
        return (
          <Typography color="text.secondary">
            Unknown agent output
          </Typography>
        );
    }
  };

  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ textTransform: 'capitalize', fontWeight: 600 }}>
          {agent} Output
        </Typography>
        
        {data.metrics && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Cost: {data.metrics.cost}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Time: {data.metrics.time}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tokens: {data.metrics.tokens}
            </Typography>
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {renderOutput()}
        
        {/* Raw Data Toggle */}
        <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Accordion>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              onClick={() => toggleSection('raw_data')}
            >
              <Typography variant="body2" color="text.secondary">
                Raw Data
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography
                  component="pre"
                  variant="caption"
                  sx={{
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    overflow: 'auto',
                    maxHeight: 400
                  }}
                >
                  {JSON.stringify(data.raw_data || data, null, 2)}
                </Typography>
              </Paper>
            </AccordionDetails>
          </Accordion>
        </Box>
      </Box>
    </Box>
  );
};

export default AgentOutput;