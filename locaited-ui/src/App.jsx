import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Alert,
} from '@mui/material';
import EventDiscoveryForm from './components/EventDiscoveryForm';
import StatusIndicator from './components/StatusIndicator';
import ResultsContainer from './components/ResultsContainer';
import DebugModal from './components/DebugModal';
import CachePreferenceDialog from './components/debug/CachePreferenceDialog';
import { discoverEvents, checkHealth } from './services/api';
import useDebugSSE from './hooks/useDebugSSE';
import useDebugStore from './stores/debugStore';

// Create theme matching logo's blue gradient
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2196F3', // Logo blue
      light: '#4ECDC4', // Logo cyan
      dark: '#1565C0', // Logo dark blue
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#4ECDC4', // Logo cyan
      light: '#80E8E0',
      dark: '#26A69A',
    },
    error: {
      main: '#F44336',
      light: '#FFEBEE',
    },
    background: {
      default: '#F8FCFF', // Very light blue tint
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1565C0', // Dark blue for text
      secondary: '#546E7A',
    },
    divider: 'rgba(33, 150, 243, 0.12)',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 16,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24)',
          transition: 'all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1)',
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.15), 0px 2px 4px rgba(0, 0, 0, 0.25)',
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 100,
          textTransform: 'none',
          fontWeight: 600,
          padding: '10px 24px',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
  },
});

// Simulated agent progress steps with retry support
const simulateAgentProgress = (setCurrentStep, setCycleCount) => {
  const steps = [1, 2, 3, 4];
  let index = 0;
  let currentCycle = 1;
  
  const interval = setInterval(() => {
    if (index < steps.length) {
      setCurrentStep(steps[index]);
      index++;
    } else if (currentCycle < 3 && Math.random() > 0.7) {
      // 30% chance of retry for demo purposes (max 3 cycles)
      currentCycle++;
      setCycleCount(currentCycle);
      index = 0; // Reset to start
      setCurrentStep(1);
    } else {
      // Complete
      setCurrentStep(5);
      clearInterval(interval);
    }
  }, 8000); // Each step takes ~8 seconds
  
  return interval;
};

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);
  const [apiHealthy, setApiHealthy] = useState(true);
  const [cycleCount, setCycleCount] = useState(0);
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const statusRef = React.useRef(null);
  const abortControllerRef = React.useRef(null);
  
  // Debug functionality
  const { startDebugRun } = useDebugSSE();
  const { toggleDebugVisibility } = useDebugStore();

  // Global keyboard shortcut handler for debug toggle
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Check for Cmd/Ctrl + Shift + X
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && (event.key === 'X' || event.key === 'x')) {
        event.preventDefault();
        toggleDebugVisibility();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [toggleDebugVisibility]);

  // Check API health on mount
  useEffect(() => {
    checkHealth().then(setApiHealthy);
  }, []);

  const handleSubmit = async (formData) => {
    setIsLoading(true);
    setError(null);
    setEvents([]);
    setMetrics(null);
    setCurrentStep(1);
    setCycleCount(1);

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    // Auto-scroll to status indicator
    setTimeout(() => {
      statusRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);

    // Start simulating agent progress
    const progressInterval = simulateAgentProgress(setCurrentStep, setCycleCount);

    try {
      const startTime = Date.now();
      const response = await discoverEvents(formData, abortControllerRef.current.signal);
      
      // Calculate processing time
      const processingTime = Math.round((Date.now() - startTime) / 1000);
      
      // Clear interval if request completes
      clearInterval(progressInterval);
      
      // Check if this was a retry cycle
      if (response.workflow_metrics?.iterations > 1) {
        setCycleCount(response.workflow_metrics.iterations);
      }
      
      // Set step to completed (5)
      setCurrentStep(5);
      
      // Wait a moment to show completion, then set results
      setTimeout(() => {
        setEvents(response.events || []);
        setMetrics({
          ...response,
          processing_time: processingTime,
        });
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      clearInterval(progressInterval);
      setIsLoading(false);
      
      // Don't show error if user cancelled
      if (!err.isCancelled) {
        setError({
          message: err.message || 'Failed to discover events',
          isNetworkError: err.isNetworkError,
        });
      }
    } finally {
      abortControllerRef.current = null;
    }
  };

  const handleDebugSubmit = async (formData) => {
    setIsDebugModalOpen(true);
    await startDebugRun(formData);
  };

  const handleDebugModalClose = () => {
    setIsDebugModalOpen(false);
  };

  const handleDebugComplete = (debugResults) => {
    // Extract events and metrics from debug results
    const publisherData = debugResults.publisher;
    if (publisherData && publisherData.decision === 'APPROVE') {
      // Set events and metrics as if it was a successful standard run
      setEvents(publisherData.events || []);
      setMetrics({
        events: publisherData.events || [],
        total_cost: debugResults.total_cost || 0,
        cache_hits: debugResults.cache_hits || 0,
        status: 'success',
        message: `Found ${publisherData.events?.length || 0} events via debug mode`,
        workflow_metrics: debugResults.workflow_metrics || {}
      });
      setCurrentStep(5); // Set to completed step
      setIsLoading(false);
      setError(null);
    }
    
    // Close debug modal
    setIsDebugModalOpen(false);
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setCurrentStep(1);
      setError({
        message: 'Discovery cancelled',
        isCancelled: true,
      });
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        {/* Main Content */}
        <Container maxWidth="lg" sx={{ mt: 6, mb: 4, px: { xs: 2, sm: 3 } }}>
          {/* Central Logo Section */}
          <Box sx={{ 
            textAlign: 'center', 
            mb: 6,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
          }}>
            <img 
              src="/logo-transparent.png" 
              alt="LocAIted Logo" 
              style={{ 
                height: 240,
                marginBottom: 0,
              }}
            />
            <Typography 
              variant="h1" 
              component="h1" 
              sx={{ 
                fontWeight: 200,
                letterSpacing: '0.12em',
                fontSize: '8rem',
                color: 'primary.main',
                fontFamily: '"Work Sans", "Inter", sans-serif',
                mb: 3,
              }}
            >
              LocAIted
            </Typography>
            <Typography 
              variant="h2" 
              sx={{ 
                color: 'text.secondary',
                fontWeight: 300,
                letterSpacing: '0.04em',
                fontSize: '3.5rem',
                fontFamily: '"Work Sans", "Inter", sans-serif',
              }}
            >
              Event Discovery for Photojournalists
            </Typography>
          </Box>
          {/* API Health Warning */}
          {!apiHealthy && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Cannot connect to API server. Please ensure the backend is running on port 8000.
            </Alert>
          )}

          {/* Form Section */}
          <EventDiscoveryForm 
            onSubmit={handleSubmit}
            onDebugSubmit={handleDebugSubmit}
            isLoading={isLoading}
          />

          {/* Status Indicator */}
          <div ref={statusRef}>
            <StatusIndicator 
              isActive={isLoading}
              currentStep={currentStep}
              cycleCount={cycleCount}
              onCancel={handleCancel}
            />
          </div>

          {/* Results Section */}
          <ResultsContainer 
            events={events}
            metrics={metrics}
            error={error}
          />
        </Container>
      </Box>

      {/* Debug Modal */}
      <DebugModal 
        isOpen={isDebugModalOpen}
        onClose={handleDebugModalClose}
        onComplete={handleDebugComplete}
      />
      
      {/* Cache Preference Dialog */}
      <CachePreferenceDialog onDebugStart={() => setIsDebugModalOpen(true)} />
    </ThemeProvider>
  );
}

export default App
