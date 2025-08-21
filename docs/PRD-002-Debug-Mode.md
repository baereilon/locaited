# PRD: Debug Mode for Agent Pipeline Visibility

## Overview
Add a debug mode to the LocAIted UI that provides step-by-step visibility into the agent pipeline, allowing users to inspect and understand what each agent produces before continuing to the next.

## User Experience

### Entry Point
- **Debug Run Button**: Separate button next to "Discover Events"
- **Keyboard Shortcut**: `Cmd/Ctrl + Shift + D` to toggle button visibility
- **Visual Design**: Distinct styling (e.g., outline button with debug icon)

### Debug Workflow

1. **User initiates debug run** → Same form validation as normal run
2. **Progress Modal Opens** → Full-screen overlay showing pipeline progress
3. **For each agent**:
   - Show agent name and status
   - Display formatted output (what it's passing to next agent)
   - Show metrics (cost, time, tokens)
   - "Continue" button to proceed (disabled while processing)
   - "Stop Debug" button to cancel
4. **On completion** → Show final results as normal

### Agent-Specific Views

#### Editor Agent Output
```
Profile Created:
- Location: New York City
- Timeframe: Next 7 days
- Interests: [protests, cultural events]

Guidance for Researcher:
"Focus on outdoor events with visual impact..."

[Metrics] Cost: $0.002 | Time: 1.2s | Tokens: 450
```

#### Researcher Agent Output
```
Generated 25 Event Leads:

1. Climate March at Washington Square Park
   Type: Protest
   Keywords: [climate, march, protest]
   Search Query: "Climate March Washington Square Park NYC"
   
2. [Truncated - showing 5 of 25]
   
[+] Show all 25 leads

[Metrics] Cost: $0.004 | Time: 2.1s | Tokens: 1200
```

#### Fact-Checker Agent Output
```
Searched for 8 Event Leads:

✓ Climate March - 3 results found
  - nytimes.com: "Activists Plan Climate March..."
  - timeout.com: "NYC Climate Week Events..."
  [+] Show all results

✓ Housing Justice Rally - 2 results found
✗ Jazz Festival - No results
  
[+] Show all searches (8)

Cache Hits: 3/8
[Metrics] Cost: $0.008 | Time: 3.5s | Searches: 8
```

#### Publisher Agent Output
```
Extracted 12 Events → Deduplicated to 10

Events for Approval:
1. Climate March (Score: 85)
   Date: 2024-03-15 | Time: 2 PM
   Location: Washington Square Park
   [+] Full details

2. [Showing 5 of 10]

Gate Decision: APPROVE
Reason: "10 high-quality events with specific dates and locations"

[Metrics] Cost: $0.006 | Time: 2.8s | Tokens: 1800
```

### Error Handling
```
❌ Agent Error: Publisher

Error: Failed to extract events from evidence
Details: Invalid JSON response from LLM

[Debug Info]
- Input size: 15KB
- Token limit: 2500
- Response: [truncated...]

[Stop Debug] [Copy Error Details]
```

## Technical Implementation

### Backend Changes

#### New Endpoint: `/workflow/discover-debug`
- Similar to `/workflow/discover` but returns intermediate results
- Uses Server-Sent Events (SSE) for streaming updates
- Each agent completion sends an event with formatted data

```python
@app.post("/workflow/discover-debug")
async def discover_debug(request: DiscoverRequest):
    async def event_generator():
        # After Editor
        yield {
            "event": "editor_complete",
            "data": {
                "profile": profile,
                "metrics": editor_metrics,
                "formatted": format_editor_output(profile)
            }
        }
        
        # Wait for client continue signal
        await continue_signal.wait()
        
        # Continue with Researcher...
```

#### Formatting Functions
Each agent gets a formatting function that creates human-readable output:
```python
def format_researcher_output(leads: List[Dict]) -> Dict:
    return {
        "summary": f"Generated {len(leads)} event leads",
        "preview": leads[:5],  # First 5 leads
        "total": len(leads),
        "types": Counter(lead["type"] for lead in leads)
    }
```

### Frontend Changes

#### Debug Mode Store
```javascript
const useDebugMode = create((set) => ({
  isDebugMode: false,
  isDebugVisible: localStorage.getItem('debugVisible') === 'true',
  currentAgent: null,
  agentResults: {},
  
  toggleDebugVisibility: () => set(state => {
    const newVisible = !state.isDebugVisible;
    localStorage.setItem('debugVisible', String(newVisible));
    return { isDebugVisible: newVisible };
  }),
  
  setAgentResult: (agent, result) => set(state => ({
    agentResults: { ...state.agentResults, [agent]: result }
  }))
}));
```

#### Debug Modal Component
```jsx
<DebugModal>
  <AgentProgress agents={AGENTS} current={currentAgent} />
  
  <AgentOutput
    agent={currentAgent}
    data={agentResults[currentAgent]}
    onExpand={handleExpand}
  />
  
  <DebugControls>
    <Button onClick={handleContinue} disabled={processing}>
      Continue to {nextAgent}
    </Button>
    <Button onClick={handleStop} variant="outline">
      Stop Debug
    </Button>
  </DebugControls>
</DebugModal>
```

### Data Storage
- Debug runs saved with `debug_mode: true` flag
- Same database schema as regular runs
- Intermediate results stored in `debug_snapshots` table

## Success Metrics
- Users can identify where/why events are being filtered out
- Reduced support requests about "missing events"
- Faster iteration on agent prompt improvements

## Implementation Priority
1. Backend SSE endpoint with pause/continue mechanism
2. Frontend debug modal with basic agent output display
3. Agent-specific formatters for readable output
4. Expand/collapse UI for detailed data
5. Keyboard shortcuts and persistence