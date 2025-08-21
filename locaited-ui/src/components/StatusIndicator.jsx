import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Typography,
  Paper,
  Chip,
  Button,
  Fade,
  StepIcon,
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  AutoAwesome as AutoAwesomeIcon,
  Search as SearchIcon,
  FactCheck as FactCheckIcon,
  Assessment as AssessmentIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { AGENT_STEPS } from '../config/constants';

// Custom step icons
const stepIcons = {
  1: <AutoAwesomeIcon />,
  2: <SearchIcon />,
  3: <FactCheckIcon />,
  4: <AssessmentIcon />,
  5: <CheckCircleIcon />,
};

const CustomStepIcon = ({ active, completed, icon }) => {
  return (
    <Box
      sx={{
        width: 44,
        height: 44,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: completed ? 'primary.main' : active ? 'primary.light' : 'grey.200',
        color: completed || active ? 'primary.contrastText' : 'text.secondary',
        transition: 'all 0.3s ease',
        transform: active ? 'scale(1.1)' : 'scale(1)',
        boxShadow: active ? '0px 4px 12px rgba(103, 80, 164, 0.3)' : 'none',
      }}
    >
      {stepIcons[icon]}
    </Box>
  );
};

const StatusIndicator = ({ isActive, currentStep, cycleCount, onCancel }) => {
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    if (isActive) {
      // Smooth progress animation
      const timer = setInterval(() => {
        setProgress((oldProgress) => {
          if (currentStep === 5) return 100;
          if (oldProgress === 100) return 100;
          const diff = Math.random() * 10;
          return Math.min(oldProgress + diff, 95);
        });
      }, 500);

      return () => {
        clearInterval(timer);
      };
    } else {
      setProgress(0);
    }
  }, [isActive, currentStep]);

  if (!isActive) {
    return null;
  }

  const activeStepIndex = AGENT_STEPS.findIndex(step => step.id === currentStep) || 0;
  const currentMessage = AGENT_STEPS[activeStepIndex]?.message || 'Processing your request...';

  return (
    <Fade in={isActive}>
      <Paper 
        elevation={0} 
        sx={{ 
          p: 4, 
          my: 4,
          border: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(135deg, rgba(103, 80, 164, 0.03) 0%, rgba(255, 255, 255, 0) 100%)',
        }}
      >
        {/* Header with cycle indicator */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 600,
                color: 'text.primary',
                mb: 0.5,
              }}
            >
              Discovering Events
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              {currentMessage}
              {cycleCount > 1 && currentStep === 1 && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: 'primary.main',
                    fontWeight: 500,
                  }}
                >
                  • Refining search approach
                </Typography>
              )}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
            {cycleCount > 1 && (
              <Chip 
                icon={<RefreshIcon sx={{ fontSize: 16 }} />}
                label={`Attempt ${cycleCount}`}
                size="small"
                sx={{
                  bgcolor: 'primary.light',
                  color: 'primary.dark',
                  fontWeight: 500,
                  borderRadius: 2,
                }}
              />
            )}
            {onCancel && currentStep !== 5 && (
              <Button
                variant="text"
                size="small"
                onClick={onCancel}
                sx={{ 
                  color: 'text.secondary',
                  fontWeight: 500,
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  }
                }}
              >
                Stop
              </Button>
            )}
          </Box>
        </Box>
        
        {/* Progress bar with better styling */}
        <Box sx={{ mb: 4 }}>
          <LinearProgress 
            variant={currentStep === 5 ? "determinate" : "determinate"} 
            value={currentStep === 5 ? 100 : progress} 
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 3,
                background: currentStep === 5 
                  ? 'linear-gradient(90deg, #4CAF50 0%, #45A049 100%)'
                  : 'linear-gradient(90deg, #6750A4 0%, #8B7AA8 100%)',
              },
            }}
          />
        </Box>

        {/* Enhanced Stepper */}
        <Stepper 
          activeStep={activeStepIndex} 
          alternativeLabel
          sx={{
            '& .MuiStepConnector-line': {
              borderColor: 'divider',
              borderTopWidth: 2,
            },
            '& .MuiStepConnector-root.Mui-completed .MuiStepConnector-line': {
              borderColor: 'primary.main',
            },
            '& .MuiStepConnector-root.Mui-active .MuiStepConnector-line': {
              borderColor: 'primary.light',
            },
          }}
        >
          {AGENT_STEPS.map((step, index) => (
            <Step key={step.id}>
              <StepLabel
                StepIconComponent={() => (
                  <CustomStepIcon
                    active={index === activeStepIndex}
                    completed={index < activeStepIndex}
                    icon={step.id}
                  />
                )}
              >
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontWeight: index === activeStepIndex ? 600 : 400,
                    color: index === activeStepIndex ? 'text.primary' : 'text.secondary',
                  }}
                >
                  {step.label}
                </Typography>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>
    </Fade>
  );
};

StatusIndicator.propTypes = {
  isActive: PropTypes.bool.isRequired,
  currentStep: PropTypes.number,
  cycleCount: PropTypes.number,
  onCancel: PropTypes.func,
};

StatusIndicator.defaultProps = {
  currentStep: 1,
  cycleCount: 1,
};

export default StatusIndicator;