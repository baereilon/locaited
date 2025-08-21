/**
 * Export events to CSV format
 * @param {Array} events - Array of event objects
 * @param {string} filename - Name for the downloaded file
 */
export const exportToCSV = (events, filename = 'locaited_events.csv') => {
  if (!events || events.length === 0) {
    alert('No events to export');
    return;
  }

  // Define CSV headers
  const headers = [
    'Title',
    'Date',
    'Time',
    'Location',
    'Access Requirements',
    'Description',
    'Score',
    'Why Recommended',
    'URL'
  ];

  // Convert events to CSV rows
  const rows = events.map(event => [
    event.title || '',
    event.date || '',
    event.time || '',
    event.location || '',
    event.access_req || '',
    // Escape quotes and commas in description
    `"${(event.summary || '').replace(/"/g, '""')}"`,
    event.score || 0,
    `"${(event.rationale || '').replace(/"/g, '""')}"`,
    event.url || ''
  ]);

  // Combine headers and rows
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  URL.revokeObjectURL(url);
};

/**
 * Parse CSV file to extract previous events
 * @param {File} file - CSV file
 * @returns {Promise<Array>} Parsed events
 */
export const parseCSV = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const lines = text.split('\n');
        
        // Skip header and empty lines
        const events = lines
          .slice(1)
          .filter(line => line.trim())
          .map(line => {
            // Basic CSV parsing (doesn't handle all edge cases)
            const values = line.split(',');
            return {
              name: values[0]?.trim(),
              date: values[1]?.trim(),
              type: values[2]?.trim(),
            };
          });
        
        resolve(events);
      } catch (error) {
        reject(new Error('Failed to parse CSV file'));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read CSV file'));
    };
    
    reader.readAsText(file);
  });
};