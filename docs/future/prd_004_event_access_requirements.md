# PRD-004: Event Access Requirements Feature

## Overview
Implement a comprehensive event access requirements system that helps photojournalists understand what credentials or permissions they need to attend and photograph events.

## Problem Statement
Photojournalists need to know in advance what type of access is required for events:
- Which events are open to the public
- Which require press credentials
- Which need special registration or tickets
- Which are invitation-only

This information is critical for planning coverage and ensuring photographers can actually attend the events they're interested in.

## Goals
1. Extract access requirement information from event sources
2. Categorize access levels in a standardized way
3. Display access requirements clearly in the UI
4. Allow filtering by access type based on user's available credentials

## User Stories

### As a photojournalist with press credentials
- I want to see which events require press passes
- I want to filter events to only show those I can access
- I want to know registration deadlines for credentialed events

### As a freelance photographer without press credentials
- I want to find public events I can photograph
- I want to know which events allow general public access
- I want to see ticketed events I could potentially purchase access to

## Feature Requirements

### 1. Access Categories
Standardize access types into clear categories:
- **Public**: Open to all, no registration required
- **Press Pass**: Requires media credentials
- **Registration**: Free but requires advance registration
- **Ticketed**: Requires purchased ticket
- **Invitation**: By invitation only
- **Restricted**: Special permissions required
- **Unknown**: Access requirements unclear

### 2. Data Extraction (Publisher Agent)
- Extract access information from event descriptions
- Look for keywords: "open to public", "press only", "RSVP required", "tickets available", etc.
- Parse registration URLs and deadlines
- Identify credential requirements

### 3. UI Components

#### Event Card Enhancement
- Visual badge/chip showing access type
- Color coding:
  - Green: Public/Open
  - Yellow: Registration/Press Pass
  - Orange: Ticketed
  - Red: Restricted/Invitation
  - Gray: Unknown
- Tooltip with detailed access information

#### Filter Options
- Checkbox filters for access types
- "Show only events I can access" toggle
- User profile setting for available credentials

### 4. User Profile Integration
Future enhancement to store user's credentials:
- Press pass (organization, expiry)
- Memberships
- Preferred access types

## Technical Implementation

### Backend Changes
1. **Publisher Agent** (`src/agents/publisher.py`):
   - Add access extraction logic to `_process_evidence_with_llm()`
   - Include in prompt: "access_req: Extract specific access requirements"
   - Standardize to categories in `_format_final_output()`

2. **API Response**:
   ```python
   {
     "access_req": "Press Pass",
     "access_details": {
       "type": "press_pass",
       "registration_url": "...",
       "deadline": "2024-08-25",
       "notes": "NYC Press Office credentials required"
     }
   }
   ```

### Frontend Changes
1. **EventCard Component**:
   - Restore Chip component for access display
   - Add getAccessColor() function
   - Include tooltip for detailed requirements

2. **EventDiscoveryForm**:
   - Add optional "My Credentials" section
   - Multi-select for available credential types

3. **ResultsContainer**:
   - Add access type filter controls
   - Update sorting to consider accessibility

## Success Metrics
- % of events with identified access requirements
- User engagement with access filters
- Reduction in "couldn't access event" feedback

## MVP Scope (Phase 1)
- Basic access categorization (Public, Press Pass, Unknown)
- Simple visual indicator on event cards
- No filtering or user profile integration

## Future Enhancements (Phase 2)
- Detailed access requirements parsing
- User credential management
- Smart filtering based on user's credentials
- Registration deadline alerts
- Direct links to credential applications

## Dependencies
- Tavily search results must include access information
- Event sources should mention access requirements
- Publisher LLM must be trained to extract this data

## Risks & Mitigations
- **Risk**: Incomplete access information in sources
  - **Mitigation**: Default to "Unknown" with suggestion to verify
  
- **Risk**: Misclassified access requirements
  - **Mitigation**: Include source link for verification

## Timeline Estimate
- MVP: 2-3 days
- Full implementation: 1 week
- User profile integration: Additional 3-4 days