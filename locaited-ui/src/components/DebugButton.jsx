import React from 'react';
import { Button, Tooltip } from '@mui/material';
import { BugReport as BugReportIcon } from '@mui/icons-material';
import useDebugStore from '../stores/debugStore';

const DebugButton = ({ onDebugRun, disabled = false }) => {
  const { isDebugVisible } = useDebugStore();

  // Don't render if not visible
  if (!isDebugVisible) {
    return null;
  }

  return (
    <Tooltip title="Debug Run - Step through each agent (Cmd/Ctrl+Shift+X to toggle)">
      <Button
        onClick={onDebugRun}
        disabled={disabled}
        variant="outlined"
        color="warning"
        startIcon={<BugReportIcon />}
        sx={{
          ml: 2,
          borderColor: 'orange.main',
          color: 'orange.main',
          '&:hover': {
            borderColor: 'orange.dark',
            backgroundColor: 'orange.light',
          },
        }}
      >
        Debug Run
      </Button>
    </Tooltip>
  );
};

export default DebugButton;