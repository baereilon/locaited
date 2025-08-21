import { useEffect, useCallback } from 'react';
import useDebugStore from '../stores/debugStore';
import { API_BASE_URL } from '../config/constants';

const useDebugSSE = () => {
  const {
    isDebugMode,
    sessionId,
    setCurrentAgent,
    setAgentResult,
    setError,
    setEventSource,
    startDebugSession,
    setProcessing,
    setWaiting,
    stopDebugSession
  } = useDebugStore();

  const startDebugRun = useCallback(async (formData) => {
    try {
      // Create EventSource for SSE connection
      const url = `${API_BASE_URL}/workflow/discover-debug`;
      
      // Convert form data to URL params for SSE
      const params = new URLSearchParams({
        location: formData.location,
        custom_location: formData.custom_location || '',
        query: formData.query,
        interest_areas: JSON.stringify(formData.interest_areas || []),
        days_ahead: formData.days_ahead || 7,
        use_cache: formData.use_cache !== false
      });

      // Make POST request to start debug session
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: formData.location,
          custom_location: formData.custom_location || null,
          query: formData.query,
          interest_areas: formData.interest_areas || [],
          days_ahead: formData.days_ahead || 7,
          use_cache: formData.use_cache !== false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Create EventSource from the response stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let buffer = '';
      
      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete messages
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  handleSSEMessage(data);
                } catch (e) {
                  console.error('Failed to parse SSE message:', e, line);
                }
              }
            }
          }
        } catch (error) {
          console.error('Stream processing error:', error);
          setError(error.message);
        }
      };

      processStream();
      
    } catch (error) {
      console.error('Failed to start debug session:', error);
      setError(error.message);
    }
  }, [setCurrentAgent, setAgentResult, setError, setEventSource, startDebugSession, setProcessing, setWaiting]);

  const handleSSEMessage = useCallback((data) => {
    console.log('SSE Message:', data);
    
    switch (data.event) {
      case 'session_start':
        startDebugSession(data.session_id);
        console.log('Debug session started:', data.session_id);
        break;
        
      case 'agent_start':
        setCurrentAgent(data.agent);
        setProcessing(true);
        setWaiting(false);
        console.log('Agent started:', data.agent);
        break;
        
      case 'agent_complete':
        setAgentResult(data.agent, data.data);
        setProcessing(false);
        setWaiting(true);
        console.log('Agent completed:', data.agent);
        break;
        
      case 'waiting_continue':
        setWaiting(true);
        setProcessing(false);
        console.log('Waiting for continue signal');
        break;
        
      case 'agent_error':
        setError(`${data.agent} failed: ${data.data.error_message}`);
        console.error('Agent error:', data);
        break;
        
      case 'workflow_complete':
        console.log('Workflow completed successfully');
        setProcessing(false);
        setWaiting(false);
        // Could show completion state here
        break;
        
      case 'workflow_error':
        setError(`Workflow failed: ${data.error}`);
        console.error('Workflow error:', data);
        break;
        
      case 'debug_stopped':
        console.log('Debug session stopped');
        stopDebugSession();
        break;
        
      default:
        console.log('Unknown SSE event:', data);
    }
  }, [
    startDebugSession,
    setCurrentAgent,
    setAgentResult,
    setError,
    setProcessing,
    setWaiting,
    stopDebugSession
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isDebugMode) {
        stopDebugSession();
      }
    };
  }, [isDebugMode, stopDebugSession]);

  return {
    startDebugRun
  };
};

export default useDebugSSE;