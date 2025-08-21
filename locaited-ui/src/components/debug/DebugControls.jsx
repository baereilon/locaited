import React from 'react';
import { Box, Button, Typography, Chip } from '@mui/material';
import {
  PlayArrow as PlayIcon,
  CheckCircle as CompleteIcon,
  Stop as StopIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import useDebugStore from '../../stores/debugStore';

const DebugControls = ({ onClose }) => {
  const { 
    currentAgent, 
    isProcessing, 
    isWaiting,
    continueToNextAgent,
    stopDebugSession 
  } = useDebugStore();

  const getNextAgent = (currentAgent) => {
    const agentOrder = ['editor', 'researcher', 'fact_checker', 'publisher'];
    const currentIndex = agentOrder.indexOf(currentAgent);
    return currentIndex >= 0 && currentIndex < agentOrder.length - 1 
      ? agentOrder[currentIndex + 1] 
      : 'completion';
  };

  const handleContinue = () => {
    continueToNextAgent();
  };

  const handleStop = () => {
    stopDebugSession();
    onClose();
  };

  const nextAgent = getNextAgent(currentAgent);
  const isLastAgent = currentAgent === 'publisher';

  const getStatusDisplay = () => {
    if (isProcessing) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircleIcon sx={{ fontSize: 8, color: 'primary.main', animation: 'pulse 2s infinite' }} />
          <Typography variant="body2" color="text.secondary">
            Running {currentAgent}...
          </Typography>
        </Box>
      );
    }
    
    if (isWaiting) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircleIcon sx={{ fontSize: 8, color: 'warning.main' }} />
          <Typography variant="body2" color="text.secondary">
            Waiting to continue to {isLastAgent ? 'completion' : nextAgent}
          </Typography>
        </Box>
      );
    }
    
    if (!currentAgent) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircleIcon sx={{ fontSize: 8, color: 'grey.400' }} />
          <Typography variant="body2" color="text.secondary">
            Debug session ready
          </Typography>
        </Box>
      );
    }

    return null;
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {/* Status Info */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {getStatusDisplay()}
      </Box>

      {/* Control Buttons */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Continue Button */}
        <Button
          onClick={handleContinue}
          disabled={!isWaiting}
          variant="contained"
          color="primary"
          startIcon={isLastAgent ? <CompleteIcon /> : <PlayIcon />}
          sx={{ minWidth: 140 }}
        >
          {isLastAgent ? 'Complete Debug' : `Continue to ${nextAgent}`}
        </Button>

        {/* Stop Button */}
        <Button
          onClick={handleStop}
          variant="outlined"
          color="inherit"
          startIcon={<StopIcon />}
        >
          Stop Debug
        </Button>
      </Box>
    </Box>
  );
};

export default DebugControls;