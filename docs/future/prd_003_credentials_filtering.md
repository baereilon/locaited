# PRD-003: Credentials-Based Event Filtering

## Overview
Add user credentials/access level to filter events based on what the photographer can actually attend.

## Background
In v1.0, we removed the credentials field to simplify the MVP. Currently:
- All events are shown regardless of access requirements
- Events display their access requirements (public, press pass, VIP)
- Users must manually determine which events they can attend

## Problem Statement
Photographers waste time reviewing events they cannot access. A photojournalist with only public access shouldn't see press-only events prominently.

## Proposed Solution

### Phase 1: Basic Filtering
Add credentials field back to user profile:
- `public_only` - Can only attend public events
- `press_pass` - Can attend public and press events  
- `vip_access` - Can attend all events

Filter or de-prioritize events based on credentials:
- Hard filter: Don't show inaccessible events
- Soft filter: Show but mark as "Requires credentials you don't have"

### Phase 2: Credential Management
- Store multiple credentials per user
- Different credentials for different organizations
- Expiration dates for credentials
- Request access workflow for specific events

### Phase 3: Smart Recommendations
- "This event requires press pass - apply here"
- "Based on your portfolio, you may qualify for..."
- Track which credentials get users into best events

## User Experience

### Profile Setup
```
Your Credentials:
☑ Public Access (default)
☐ Press Pass - [Upload/Verify]
☐ NYPD Press Card - [Upload/Verify]
☐ UN Correspondent Pass - [Upload/Verify]
```

### Event Display
```
[Event Card]
Access: Press Pass Required ⚠️
You don't have this credential. [Request Access]
```

## Technical Implementation

### API Changes
```json
// Request
{
  "credentials": ["public", "press_pass"],
  "filter_by_access": true  // or false to see all
}

// Response event includes
{
  "access_req": "press_pass",
  "can_attend": true,
  "credential_match": "press_pass"
}
```

### Scoring Adjustment
- Events user can't attend: -20 points
- Events user can attend: normal score
- Events where user has special access: +10 points

## Success Metrics
- Reduction in time reviewing inaccessible events
- Increase in actual event attendance rate
- User satisfaction with relevance

## Dependencies
- User authentication system (for storing credentials)
- Profile persistence
- Possibly credential verification service

## Timeline Estimate
- Phase 1: 1 week (basic filtering)
- Phase 2: 2-3 weeks (credential management)
- Phase 3: 4-6 weeks (smart recommendations)

## Priority
Medium - Nice to have but not critical for MVP

## Notes
- Removed from v1.0 on 2024-08-20 to simplify initial release
- Some photographers prefer seeing all events to decide if worth getting credentials
- Consider making this an optional filter rather than mandatory