import { create } from 'zustand';

const useDebugStore = create((set, get) => ({
  // Debug visibility and mode  
  isDebugVisible: false, // Always start hidden
  isDebugMode: false,
  
  // Session state
  sessionId: null,
  currentAgent: null,
  agentResults: {},
  isProcessing: false,
  isWaiting: false,
  
  // Debug flow state
  isAskingCachePreference: false,
  pendingFormData: null,
  
  // EventSource for SSE
  eventSource: null,
  
  // Error state
  error: null,
  
  // Actions
  toggleDebugVisibility: () => {
    set((state) => {
      const newVisible = !state.isDebugVisible;
      if (newVisible) {
        localStorage.setItem('debugVisible', 'true');
      } else {
        localStorage.removeItem('debugVisible'); // Remove instead of setting to false
      }
      return { isDebugVisible: newVisible };
    });
  },
  
  startDebugSession: (sessionId) => {
    set({
      isDebugMode: true,
      sessionId,
      currentAgent: null,
      agentResults: {},
      isProcessing: true,
      isWaiting: false,
      error: null
    });
  },
  
  setCurrentAgent: (agent) => {
    set({ currentAgent: agent, isProcessing: true, isWaiting: false });
  },
  
  setAgentResult: (agent, data) => {
    set((state) => ({
      agentResults: { ...state.agentResults, [agent]: data },
      isProcessing: false,
      isWaiting: true
    }));
  },
  
  setWaiting: (waiting) => {
    set({ isWaiting: waiting });
  },
  
  setProcessing: (processing) => {
    set({ isProcessing: processing });
  },
  
  setError: (error) => {
    set({ error, isProcessing: false, isWaiting: false });
  },
  
  // Cache preference methods
  startCachePrompt: (formData) => {
    set({
      isAskingCachePreference: true,
      pendingFormData: formData,
      error: null
    });
  },
  
  cancelCachePrompt: () => {
    set({
      isAskingCachePreference: false,
      pendingFormData: null
    });
  },
  
  setEventSource: (eventSource) => {
    set({ eventSource });
  },
  
  stopDebugSession: () => {
    const { eventSource, sessionId } = get();
    
    // Close EventSource if exists
    if (eventSource) {
      eventSource.close();
    }
    
    // Send stop signal to backend if session exists
    if (sessionId) {
      fetch(`/api/workflow/debug-stop/${sessionId}`, { method: 'POST' })
        .catch(console.error); // Ignore errors on cleanup
    }
    
    set({
      isDebugMode: false,
      sessionId: null,
      currentAgent: null,
      agentResults: {},
      isProcessing: false,
      isWaiting: false,
      error: null,
      eventSource: null
    });
  },
  
  continueToNextAgent: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    
    try {
      set({ isWaiting: false, isProcessing: true });
      
      const response = await fetch(`/api/workflow/debug-continue/${sessionId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to continue debug session');
      }
    } catch (error) {
      console.error('Error continuing debug session:', error);
      set({ error: error.message });
    }
  },
  
  // Computed getters
  getAgentStatus: (agent) => {
    const { currentAgent, agentResults, isProcessing, isWaiting } = get();
    
    if (agentResults[agent]) {
      return 'completed';
    } else if (currentAgent === agent && isProcessing) {
      return 'processing';
    } else if (currentAgent === agent && isWaiting) {
      return 'waiting';
    } else {
      return 'pending';
    }
  },
  
  getAllAgentStatuses: () => {
    const agents = ['editor', 'researcher', 'fact_checker', 'publisher'];
    const { getAgentStatus } = get();
    
    return agents.reduce((statuses, agent) => {
      statuses[agent] = getAgentStatus(agent);
      return statuses;
    }, {});
  },
  
  // Reset just results (for new debug run)
  resetResults: () => {
    set({
      agentResults: {},
      currentAgent: null,
      isProcessing: false,
      isWaiting: false,
      error: null
    });
  }
}));

export default useDebugStore;