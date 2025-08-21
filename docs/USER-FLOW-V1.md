# LocAIted User Flow v1.0 - Single Flow Architecture

## Overview
LocAIted v1.0 implements a single, streamlined user flow where users provide both profile information and query details in one interaction, receive agent-processed results, and can export them. This document serves as the technical specification for this flow.

## Flow Definition

```
User Input (Profile + Query) → API Processing → Agent Pipeline → Results Display
```

### Single Interaction Model
- No separate onboarding flow
- No user authentication or persistence
- No feedback collection loop
- One form submission → One set of results

## API Contract

### Endpoint
`POST /workflow/discover`

### Request Format (ExtendedSearchRequest)
```json
{
  "location": "NYC",              // One of: NYC, DC, LA, Chicago, Boston, custom
  "custom_location": "Brooklyn",   // Required when location="custom", null otherwise
  "interest_areas": [              // Array, min 1, max 5 items
    "protests",
    "cultural",
    "political"
  ],
  "csv_file": "base64_string",    // Optional: base64 encoded CSV of previous events
  "days_ahead": 7,                 // One of: 7, 14, 30
  "query": "climate protests",     // Required: 10-200 characters
  "use_cache": true                // Default: true
}
```

**Note**: Credentials field removed in v1.0 for simplicity. Events show access requirements but no filtering is applied.

### Response Format (WorkflowResponse)
```json
{
  "events": [
    {
      "title": "Climate March at City Hall",
      "date": "2024-08-25",
      "time": "2:00 PM",           // CRITICAL: Must be prominently extracted
      "location": "City Hall, NYC",
      "access_req": "press_pass",  // One of: public_only, press_pass, vip_access, unknown
      "summary": "Large climate protest expected",
      "score": 85.5,               // 0-100 photo opportunity score
      "rationale": "High visual impact, timely issue",
      "url": "https://source.com/event"
    }
  ],
  "total_cost": 0.0234,
  "cache_hits": 5,
  "status": "success",             // One of: success, error, no_results
  "message": "Found 12 events"
}
```

## Field Requirements

### Critical Fields (Must Have)
1. **title** - Clear event name
2. **date** - Specific date (not relative)
3. **time** - Start time (valuable when available, helps photographers plan their day)
4. **location** - Precise enough to plan commute

### Important Fields
- **access_req** - Determines if photographer can attend
- **score** - Helps prioritize which events to cover
- **rationale** - Explains why event was recommended

### Optional Fields
- **url** - Source link for verification
- **summary** - Additional context

## Agent Processing Pipeline

### 1. Editor Agent
**Input:** User's combined profile + query
**Output:** Search profile with guidance for Researcher
```json
{
  "location": "NYC",
  "time_frame": "next 7 days",
  "interests": ["protests", "cultural"],
  "researcher_guidance": "Focus on climate protests and art exhibitions",
  "iteration": 1
}
```

### 2. Researcher Agent
**Input:** Editor's profile
**Output:** 25 specific event leads
```json
{
  "leads": [
    {
      "description": "Climate protest at City Hall on August 25",
      "search_query": "NYC City Hall climate protest August 25 2024",
      "type": "protest"
    }
  ]
}
```

### 3. Fact-Checker Agent
**Input:** Researcher's leads
**Output:** Web search evidence for each lead
```json
{
  "evidence": [
    {
      "lead": {...},
      "results": [
        {
          "url": "https://source.com",
          "title": "Climate Activists Plan Major Rally",
          "content": "...event details..."
        }
      ]
    }
  ]
}
```

### 4. Publisher Agent
**Input:** Fact-Checker's evidence
**Output:** Extracted and scored events
- Extracts concrete event details from evidence
- **MUST extract TIME information when available**
- Scores events 0-100 for photo opportunity
- Deduplicates similar events
- Returns max 15 events to prevent JSON overflow

## Validation Rules

### Frontend Validation
1. **Interest Areas**: 1-5 selections required
2. **Query**: 10-200 characters
3. **Custom Location**: Required when location="custom"

### Backend Validation
1. **Time Constraints**: Events must be within requested timeframe
2. **Location Match**: Events should match specified location
3. **Deduplication**: Remove duplicate events (same title, date, location)

## User Interface Behavior

### Form Submission
1. All fields validated before submission
2. Form disabled during processing
3. Clear button resets all fields

### Status Display
Shows agent-specific messages in sequence:
1. "Editor is building your profile..."
2. "Researcher is surfacing potential events..."
3. "Fact-Checker is gathering event details..."
4. "Publisher is evaluating if events are worth your time..."

### Results Display
1. Events sorted by date (default) or score
2. TIME displayed prominently in large, bold text
3. Access requirements shown as colored badges
4. Photo score shown as visual progress bar
5. CSV export includes all fields

## Success Metrics

### North Star Metrics (Backend must optimize for these)
1. **Number of Interesting Events** - Quality over quantity
2. **Events with Complete Info** - Must have title, date, location
3. **Minimal Duplicates** - Effective deduplication

### Technical Metrics
- Response time: Target < 60 seconds
- Cost per query: Target < $0.05
- Cache hit rate: Target > 60%

## Error Handling

### API Errors
```json
{
  "status": "error",
  "message": "Detailed error message",
  "events": []  // Empty array
}
```

### Network Errors
Frontend displays: "Cannot connect to API server. Please ensure the backend is running on port 8000."

### No Results
```json
{
  "status": "no_results",
  "message": "No events found matching your criteria",
  "events": []
}
```

## Caching Strategy

### What Gets Cached
1. Tavily search results (by query hash)
2. LLM responses (by input hash)
3. Complete workflow results (optional)

### Cache Duration
- Default: 24 hours
- Configurable via environment variables

## Future Compatibility

### Do NOT Break These
1. The `/workflow/discover` endpoint contract
2. Required fields in event objects
3. TIME field extraction when available
4. Score range (0-100)

### Safe to Modify
1. Add new optional fields to events
2. Improve extraction algorithms
3. Add new agent steps (if backward compatible)
4. Enhance scoring logic

## Implementation Notes

### Current Limitations
1. No user persistence - each session is independent
2. CSV parsing is basic - complex formats may fail
3. Custom location is free text - no validation
4. No real-time updates during processing

### Known Issues
1. TIME extraction sometimes misses specific times
2. Date constraints not always enforced (may return past events)
3. Publisher limited to 15 events to prevent JSON errors

## Testing Requirements

### Critical Paths to Test
1. Form validation → API call → Results display
2. All required fields present in response
3. TIME field properly extracted and displayed
4. CSV export functionality
5. Error states handled gracefully

## Version History

### v1.0 (Current)
- Single-flow architecture
- No authentication
- Basic CSV support
- 15 event limit

### v2.0 (Planned)
- User authentication
- Profile persistence
- Feedback collection
- Event history