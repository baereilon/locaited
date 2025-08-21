import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Select,
  MenuItem,
  TextField,
  Chip,
  Stack,
  Typography,
  Alert,
  InputLabel,
  OutlinedInput,
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  Clear as ClearIcon, 
  Search as SearchIcon,
  LocationOn as LocationIcon,
  CalendarMonth as CalendarIcon,
  Interests as InterestsIcon,
} from '@mui/icons-material';
import { LOCATIONS, CREDENTIALS, INTEREST_AREAS, TIME_WINDOWS } from '../config/constants';
import DebugButton from './DebugButton';

const EventDiscoveryForm = ({ onSubmit, onDebugSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    location: 'NYC',
    customLocation: '',
    interestAreas: [],
    csvFile: null,
    daysAhead: 7,
    query: '',
  });

  const [errors, setErrors] = useState({});
  const [showCustomLocation, setShowCustomLocation] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    // Validate interest areas
    if (formData.interestAreas.length === 0) {
      newErrors.interestAreas = 'Please select at least one interest area';
    } else if (formData.interestAreas.length > 5) {
      newErrors.interestAreas = 'Please select no more than 5 interest areas';
    }

    // Validate query
    if (!formData.query.trim()) {
      newErrors.query = 'Please describe what events you are looking for';
    } else if (formData.query.length < 10) {
      newErrors.query = 'Please provide more detail (minimum 10 characters)';
    } else if (formData.query.length > 200) {
      newErrors.query = 'Please keep your description under 200 characters';
    }

    // Validate custom location if selected
    if (showCustomLocation && !formData.customLocation.trim()) {
      newErrors.customLocation = 'Please enter a custom location';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLocationChange = (event) => {
    const value = event.target.value;
    setFormData({ ...formData, location: value });
    setShowCustomLocation(value === 'custom');
    if (value !== 'custom') {
      setFormData({ ...formData, location: value, customLocation: '' });
    }
  };

  const handleInterestToggle = (interest) => {
    const currentInterests = formData.interestAreas;
    const newInterests = currentInterests.includes(interest)
      ? currentInterests.filter(i => i !== interest)
      : [...currentInterests, interest];
    
    setFormData({ ...formData, interestAreas: newInterests });
    
    // Clear error if valid
    if (newInterests.length > 0 && newInterests.length <= 5) {
      setErrors({ ...errors, interestAreas: undefined });
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/csv') {
      setFormData({ ...formData, csvFile: file });
    } else if (file) {
      alert('Please upload a CSV file');
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Prepare submission data
    const submissionData = {
      location: showCustomLocation ? 'custom' : formData.location,
      custom_location: showCustomLocation ? formData.customLocation : null,
      interest_areas: formData.interestAreas,
      csv_file: formData.csvFile ? 'base64_encoded_file' : null, // Would need actual encoding
      days_ahead: formData.daysAhead,
      query: formData.query,
      use_cache: true,
    };

    onSubmit(submissionData);
  };

  const handleDebugSubmit = () => {
    if (!validateForm()) return;

    const submissionData = {
      location: formData.location,
      custom_location: showCustomLocation ? formData.customLocation : null,
      interest_areas: formData.interestAreas,
      csv_file: null, // TODO: Handle CSV upload in debug mode
      days_ahead: formData.daysAhead,
      query: formData.query,
      use_cache: true,
    };

    onDebugSubmit(submissionData);
  };

  const handleClear = () => {
    setFormData({
      location: 'NYC',
      customLocation: '',
      interestAreas: [],
      csvFile: null,
      daysAhead: 7,
      query: '',
    });
    setErrors({});
    setShowCustomLocation(false);
  };

  return (
    <Box>
      <form onSubmit={handleSubmit}>
        <Stack spacing={4}>
          <Box>
            <Typography 
              variant="h5" 
              component="h2"
              sx={{ 
                fontWeight: 700,
                color: 'text.primary',
                mb: 1,
              }}
            >
              Discover Events
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Find photojournalism opportunities tailored to your interests
            </Typography>
          </Box>

          {/* Profile Section */}
          <Box 
            sx={{ 
              p: 3,
              bgcolor: 'background.paper',
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Typography 
              variant="h6" 
              sx={{ 
                mb: 3,
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <LocationIcon color="primary" />
              Profile Information
            </Typography>
            
            {/* Location */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Location</InputLabel>
              <Select
                value={formData.location}
                onChange={handleLocationChange}
                label="Location"
              >
                {LOCATIONS.map(loc => (
                  <MenuItem key={loc.value} value={loc.value}>
                    {loc.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Custom Location */}
            {showCustomLocation && (
              <TextField
                fullWidth
                label="Custom Location"
                value={formData.customLocation}
                onChange={(e) => setFormData({ ...formData, customLocation: e.target.value })}
                error={!!errors.customLocation}
                helperText={errors.customLocation}
                sx={{ mb: 2 }}
              />
            )}


            {/* Interest Areas */}
            <FormControl fullWidth error={!!errors.interestAreas} sx={{ mb: 2 }}>
              <FormLabel 
                component="legend"
                sx={{ 
                  fontWeight: 500,
                  color: 'text.primary',
                  mb: 1.5,
                }}
              >
                Interest Areas (Select 1-5)
              </FormLabel>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {INTEREST_AREAS.map(interest => (
                  <Chip
                    key={interest}
                    label={interest}
                    onClick={() => handleInterestToggle(interest.toLowerCase())}
                    sx={{
                      borderRadius: 2,
                      fontWeight: formData.interestAreas.includes(interest.toLowerCase()) ? 600 : 400,
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
                      },
                    }}
                    color={formData.interestAreas.includes(interest.toLowerCase()) ? 'primary' : 'default'}
                    variant={formData.interestAreas.includes(interest.toLowerCase()) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
              {errors.interestAreas && (
                <Typography color="error" variant="caption" sx={{ mt: 1 }}>
                  {errors.interestAreas}
                </Typography>
              )}
            </FormControl>

            {/* CSV Upload */}
            <Box sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                component="label"
                startIcon={<UploadIcon />}
              >
                {formData.csvFile ? formData.csvFile.name : 'Upload Previous Events (Optional)'}
                <input
                  type="file"
                  accept=".csv"
                  hidden
                  onChange={handleFileUpload}
                />
              </Button>
              {formData.csvFile && (
                <Button
                  size="small"
                  onClick={() => setFormData({ ...formData, csvFile: null })}
                  sx={{ ml: 1 }}
                >
                  Remove
                </Button>
              )}
            </Box>
          </Box>

          {/* Query Section */}
          <Box 
            sx={{ 
              p: 3,
              bgcolor: 'background.paper',
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Typography 
              variant="h6" 
              sx={{ 
                mb: 3,
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <CalendarIcon color="primary" />
              Query Details
            </Typography>

            {/* Time Window */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Time Window</InputLabel>
              <Select
                value={formData.daysAhead}
                onChange={(e) => setFormData({ ...formData, daysAhead: e.target.value })}
                label="Time Window"
              >
                {TIME_WINDOWS.map(window => (
                  <MenuItem key={window.value} value={window.value}>
                    {window.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Looking For */}
            <TextField
              fullWidth
              multiline
              rows={2}
              label="What events are you looking for?"
              placeholder="e.g., climate protests, art gallery openings"
              value={formData.query}
              onChange={(e) => setFormData({ ...formData, query: e.target.value })}
              error={!!errors.query}
              helperText={errors.query || `${formData.query.length}/200 characters`}
            />
          </Box>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button
              variant="text"
              onClick={handleClear}
              disabled={isLoading}
              sx={{ 
                color: 'text.secondary',
                fontWeight: 500,
              }}
            >
              Clear Form
            </Button>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SearchIcon />}
                disabled={isLoading}
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  boxShadow: '0px 4px 12px rgba(103, 80, 164, 0.2)',
                  '&:hover': {
                    boxShadow: '0px 6px 16px rgba(103, 80, 164, 0.3)',
                  },
                }}
              >
                Discover Events
              </Button>
              
              <DebugButton 
                onDebugRun={handleDebugSubmit}
                disabled={isLoading}
              />
            </Box>
          </Stack>
        </Stack>
      </form>
    </Box>
  );
};

EventDiscoveryForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onDebugSubmit: PropTypes.func,
  isLoading: PropTypes.bool,
};

EventDiscoveryForm.defaultProps = {
  onDebugSubmit: () => {},
  isLoading: false,
};

export default EventDiscoveryForm;