import React, { useEffect } from 'react';
import { Button, Tooltip } from '@mui/material';
import { BugReport as BugReportIcon } from '@mui/icons-material';
import useDebugStore from '../stores/debugStore';

const DebugButton = ({ onDebugRun, disabled = false }) => {
  const { isDebugVisible, toggleDebugVisibility } = useDebugStore();

  // Keyboard shortcut handler
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Check for Cmd/Ctrl + Shift + D
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        toggleDebugVisibility();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [toggleDebugVisibility]);

  // Don't render if not visible
  if (!isDebugVisible) {
    return null;
  }

  return (
    <Tooltip title="Debug Run - Step through each agent (Cmd/Ctrl+Shift+D to toggle)">
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