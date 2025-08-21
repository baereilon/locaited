// Application constants

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const LOCATIONS = [
  { value: 'NYC', label: 'New York City' },
  { value: 'DC', label: 'Washington DC' },
  { value: 'LA', label: 'Los Angeles' },
  { value: 'Chicago', label: 'Chicago' },
  { value: 'Boston', label: 'Boston' },
  { value: 'custom', label: 'Custom Location' }
];

export const CREDENTIALS = [
  { value: 'public_only', label: 'Public Only' },
  { value: 'press_pass', label: 'Press Pass' },
  { value: 'vip_access', label: 'VIP Access' }
];

export const INTEREST_AREAS = [
  'Protests',
  'Cultural',
  'Political',
  'Fashion',
  'Sports',
  'Tech',
  'Arts'
];

export const TIME_WINDOWS = [
  { value: 7, label: 'Next 7 days' },
  { value: 14, label: 'Next 14 days' },
  { value: 30, label: 'Next 30 days' }
];

export const AGENT_STEPS = [
  { id: 1, label: 'Editor', message: 'Editor is building your profile...' },
  { id: 2, label: 'Researcher', message: 'Researcher is surfacing potential events...' },
  { id: 3, label: 'Fact-Checker', message: 'Fact-Checker is gathering event details...' },
  { id: 4, label: 'Publisher', message: 'Publisher is evaluating if events are worth your time...' },
  { id: 5, label: 'Complete', message: 'Processing complete! Results are ready.' }
];