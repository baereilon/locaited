import React from 'react';
import {
  Box,
  Typography,
  Chip,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
  stepConnectorClasses,
  styled
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Circle as CircleIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import useDebugStore from '../../stores/debugStore';

const ColorlibConnector = styled(StepConnector)(({ theme, status }) => ({
  [`&.${stepConnectorClasses.alternativeLabel}`]: {
    top: 22,
  },
  [`&.${stepConnectorClasses.active}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      backgroundImage: status === 'completed' 
        ? `linear-gradient( 95deg, ${theme.palette.success.main} 0%, ${theme.palette.success.main} 50%, ${theme.palette.success.main} 100%)`
        : `linear-gradient( 95deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.main} 50%, ${theme.palette.primary.main} 100%)`,
    },
  },
  [`&.${stepConnectorClasses.completed}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      backgroundImage: `linear-gradient( 95deg, ${theme.palette.success.main} 0%, ${theme.palette.success.main} 50%, ${theme.palette.success.main} 100%)`,
    },
  },
  [`& .${stepConnectorClasses.line}`]: {
    height: 3,
    border: 0,
    backgroundColor: theme.palette.grey[300],
    borderRadius: 1,
  },
}));

const AgentProgress = () => {
  const { getAllAgentStatuses } = useDebugStore();
  
  const agents = [
    { key: 'editor', name: 'Editor', description: 'Building search profile' },
    { key: 'researcher', name: 'Researcher', description: 'Generating event leads' },
    { key: 'fact_checker', name: 'Fact-Checker', description: 'Gathering evidence' },
    { key: 'publisher', name: 'Publisher', description: 'Extracting events' }
  ];

  const statuses = getAllAgentStatuses();

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return (
          <Box sx={{ 
            width: 32, 
            height: 32, 
            bgcolor: 'success.light', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <CheckIcon sx={{ fontSize: 20, color: 'success.main' }} />
          </Box>
        );
      case 'processing':
        return (
          <Box sx={{ 
            width: 32, 
            height: 32, 
            bgcolor: 'primary.light', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <CircularProgress size={16} sx={{ color: 'primary.main' }} />
          </Box>
        );
      case 'waiting':
        return (
          <Box sx={{ 
            width: 32, 
            height: 32, 
            bgcolor: 'warning.light', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <ScheduleIcon sx={{ fontSize: 20, color: 'warning.main' }} />
          </Box>
        );
      default:
        return (
          <Box sx={{ 
            width: 32, 
            height: 32, 
            bgcolor: 'grey.100', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <CircleIcon sx={{ fontSize: 12, color: 'grey.400' }} />
          </Box>
        );
    }
  };

  const getStatusChip = (status, agentName) => {
    const chipProps = {
      size: 'small',
      label: agentName
    };

    switch (status) {
      case 'completed':
        return <Chip {...chipProps} color="success" variant="filled" />;
      case 'processing':
        return <Chip {...chipProps} color="primary" variant="filled" />;
      case 'waiting':
        return <Chip {...chipProps} color="warning" variant="filled" />;
      default:
        return <Chip {...chipProps} color="default" variant="outlined" />;
    }
  };

  const activeStep = agents.findIndex(agent => 
    statuses[agent.key] === 'processing' || statuses[agent.key] === 'waiting'
  );

  const completedCount = Object.values(statuses).filter(s => s === 'completed').length;

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        Pipeline Progress
      </Typography>
      
      <Stepper 
        activeStep={activeStep === -1 ? agents.length : activeStep} 
        alternativeLabel
        connector={<ColorlibConnector />}
      >
        {agents.map((agent, index) => {
          const status = statuses[agent.key];
          const isCompleted = status === 'completed';
          
          return (
            <Step key={agent.key} completed={isCompleted}>
              <StepLabel
                StepIconComponent={() => getStatusIcon(status)}
                sx={{
                  '& .MuiStepLabel-label': {
                    mt: 1,
                    fontSize: '0.875rem'
                  }
                }}
              >
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                  {getStatusChip(status, agent.name)}
                  <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 120, textAlign: 'center' }}>
                    {agent.description}
                  </Typography>
                </Box>
              </StepLabel>
            </Step>
          );
        })}
      </Stepper>
      
      {/* Status Summary */}
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {completedCount} of {agents.length} agents completed
        </Typography>
      </Box>
    </Box>
  );
};

export default AgentProgress;