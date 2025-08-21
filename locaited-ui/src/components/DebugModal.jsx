import React, { useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  IconButton,
  Paper,
  Button,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  ErrorOutline as ErrorIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import useDebugStore from '../stores/debugStore';
import AgentProgress from './debug/AgentProgress';
import AgentOutput from './debug/AgentOutput';
import DebugControls from './debug/DebugControls';

const DebugModal = ({ isOpen, onClose }) => {
  const { 
    isDebugMode, 
    currentAgent, 
    agentResults, 
    error,
    stopDebugSession 
  } = useDebugStore();

  // Close modal when debug session ends
  useEffect(() => {
    if (!isDebugMode && isOpen) {
      onClose();
    }
  }, [isDebugMode, isOpen, onClose]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isDebugMode) {
        stopDebugSession();
      }
    };
  }, []);

  return (
    <Dialog
      open={isOpen && isDebugMode}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      {/* Header */}
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircleIcon 
              sx={{ 
                color: 'orange.main', 
                fontSize: 12,
                animation: 'pulse 2s infinite'
              }} 
            />
            <Typography variant="h6" component="h2">
              Debug Mode - Agent Pipeline
            </Typography>
          </Box>
          
          <IconButton
            onClick={onClose}
            color="inherit"
            aria-label="Close Debug"
            title="Close Debug (stops current session)"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      {/* Progress Section */}
      <Paper sx={{ m: 2, p: 3, elevation: 1 }}>
        <AgentProgress />
      </Paper>

      {/* Main Content */}
      <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', p: 0 }}>
        {error ? (
          <Box sx={{ 
            p: 4, 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <Box sx={{ textAlign: 'center' }}>
              <Box sx={{ 
                width: 64, 
                height: 64, 
                bgcolor: 'error.light', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                mx: 'auto',
                mb: 2
              }}>
                <ErrorIcon sx={{ fontSize: 32, color: 'error.main' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                Debug Session Error
              </Typography>
              <Typography color="text.secondary" paragraph>
                {error}
              </Typography>
              <Button
                onClick={onClose}
                variant="contained"
                color="error"
              >
                Close Debug
              </Button>
            </Box>
          </Box>
        ) : (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Agent Output */}
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              <AgentOutput 
                agent={currentAgent} 
                data={currentAgent ? agentResults[currentAgent] : null} 
              />
            </Box>

            {/* Controls */}
            <Paper sx={{ p: 3, elevation: 1 }}>
              <DebugControls onClose={onClose} />
            </Paper>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default DebugModal;