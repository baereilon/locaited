import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  Alert,
  Chip
} from '@mui/material';
import {
  Storage as CacheIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  MonetizationOn as CostIcon
} from '@mui/icons-material';
import useDebugStore from '../../stores/debugStore';
import useDebugSSE from '../../hooks/useDebugSSE';

const CachePreferenceDialog = ({ onDebugStart }) => {
  const { 
    isAskingCachePreference, 
    pendingFormData, 
    cancelCachePrompt 
  } = useDebugStore();
  
  const { startDebugRun } = useDebugSSE();

  const handleCacheChoice = async (useCache) => {
    if (!pendingFormData) return;
    
    // Update form data with cache preference
    const formDataWithCache = {
      ...pendingFormData,
      use_cache: useCache
    };
    
    // Close dialog
    cancelCachePrompt();
    
    // Open debug modal immediately
    if (onDebugStart) {
      onDebugStart();
    }
    
    // Small delay to ensure modal opens before starting SSE
    setTimeout(async () => {
      await startDebugRun(formDataWithCache);
    }, 100);
  };

  const handleCancel = () => {
    cancelCachePrompt();
  };

  return (
    <Dialog
      open={isAskingCachePreference}
      onClose={handleCancel}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
        }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CacheIcon color="primary" />
          <Typography variant="h6" component="span">
            Cache Preference
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Typography variant="body1" gutterBottom>
          Choose whether to use cached results or generate fresh data:
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 3 }}>
          {/* Use Cache Option */}
          <Alert 
            severity="info" 
            sx={{ 
              bgcolor: 'primary.light',
              '& .MuiAlert-message': { width: '100%' }
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Use Cache (Faster)
                </Typography>
                <Typography variant="body2">
                  Use previously generated results if available
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip icon={<SpeedIcon />} label="Fast" size="small" color="primary" />
                <Chip icon={<CostIcon />} label="$0" size="small" color="success" />
              </Box>
            </Box>
          </Alert>
          
          {/* Fresh Generation Option */}
          <Alert 
            severity="warning"
            sx={{ 
              bgcolor: 'warning.light',
              '& .MuiAlert-message': { width: '100%' }
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Generate Fresh (Slower)
                </Typography>
                <Typography variant="body2">
                  Generate new results with latest validation
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip icon={<RefreshIcon />} label="Fresh" size="small" color="warning" />
                <Chip icon={<CostIcon />} label="~$0.02" size="small" color="error" />
              </Box>
            </Box>
          </Alert>
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Fresh generation uses enhanced validation with up to 10 LLM calls to ensure event quality and URLs.
        </Typography>
      </DialogContent>
      
      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button
          onClick={handleCancel}
          color="inherit"
        >
          Cancel
        </Button>
        <Button
          onClick={() => handleCacheChoice(true)}
          variant="outlined"
          color="primary"
          startIcon={<CacheIcon />}
        >
          Use Cache
        </Button>
        <Button
          onClick={() => handleCacheChoice(false)}
          variant="contained"
          color="warning"
          startIcon={<RefreshIcon />}
        >
          Generate Fresh
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CachePreferenceDialog;