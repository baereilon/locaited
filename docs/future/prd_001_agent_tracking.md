# PRD-001: Enhanced Agent Tracking

**Status**: Proposed  
**Priority**: High  
**Effort**: Small  
**Created**: 2025-08-20  

## Problem Statement

Currently, when validating events, we cannot directly trace which Researcher lead became which Publisher event. The workflow state contains all the data (leads, evidence, events) but lacks explicit connections between them. This makes it difficult to:

1. Understand why certain leads didn't become events
2. Debug issues in the pipeline
3. Optimize agent performance based on success rates

## User Impact

**For Developers**:
- Clear visibility into the data transformation pipeline
- Easier debugging when events are missed
- Better optimization insights

**For End Users**:
- Improved event discovery as we can identify and fix pipeline bottlenecks
- Higher quality results from better-tuned agents

## Proposed Solution

Add tracking IDs and mappings throughout the workflow to create explicit connections:

```python
# Each lead gets a unique ID
lead = {
    'id': 'lead_001',
    'description': 'Climate protest at Foley Square',
    ...
}

# Evidence references the lead it came from
evidence = {
    'lead_id': 'lead_001',
    'search_results': [...],
    ...
}

# Event references its source lead and evidence
event = {
    'id': 'event_001',
    'source_lead_id': 'lead_001',
    'source_evidence_ids': ['evidence_001', 'evidence_002'],
    'title': 'NYC Climate Strike',
    ...
}
```

## Technical Approach

### 1. Modify Researcher Agent
```python
# In researcher_v4.py
def process(self, state):
    leads = self._generate_leads(...)
    # Add unique IDs
    for i, lead in enumerate(leads):
        lead['id'] = f"lead_{i+1:03d}"
    return {'leads': leads}
```

### 2. Modify Fact-Checker Agent
```python
# In fact_checker_v4.py
def process(self, state):
    evidence_list = []
    for lead in state['leads']:
        evidence = self._search_evidence(lead)
        evidence['lead_id'] = lead['id']
        evidence['id'] = f"evidence_{lead['id']}"
        evidence_list.append(evidence)
    return {'evidence': evidence_list}
```

### 3. Modify Publisher Agent
```python
# In publisher_v4.py
def _extract_events(self, evidence):
    # Keep track of which evidence created which event
    events = []
    for evt in extracted_events:
        evt['source_lead_id'] = evidence['lead_id']
        evt['source_evidence_id'] = evidence['id']
        events.append(evt)
    
    # Return ALL extracted events, not just top 10
    return {
        'all_extracted_events': events,  # All 15-20 events
        'approved_events': top_10,       # Top scored
        'event_mappings': mappings       # Tracking data
    }
```

### 4. Update Validation Output
Create comprehensive tracking CSV:
```csv
event_title,lead_id,lead_description,evidence_found,evidence_count,final_score,was_approved
NYC Climate Strike,lead_001,Climate protest at Foley Square,Yes,10,90,Yes
[Event that didn't make it],lead_002,...,Yes,5,60,No
[Lead with no evidence],lead_003,...,No,0,0,No
```

## Implementation Phases

**Phase 1: Add ID Infrastructure**
- Add ID generation to Researcher
- Update data structures to include ID fields
- Verify IDs flow through pipeline

**Phase 2: Implement Tracking**
- Add lead_id references in Fact-Checker
- Add source tracking in Publisher
- Ensure mappings are preserved in state

**Phase 3: Update Outputs**
- Modify validation scripts to use tracking
- Generate tracking CSV
- Test end-to-end traceability

## Dependencies

- No external dependencies
- Backward compatible (IDs are additional fields)
- Can be rolled out incrementally

## Success Metrics

1. **Traceability**: 100% of events can be traced to their source leads
2. **Optimization Insights**: Identify which types of leads have highest success rate
3. **Lead Conversion Rate**: Measure what percentage of leads become final events

## Open Questions

1. Should we store mappings in a separate file or embed in the state?
2. Do we need to track timing (how long each transformation took)?
3. Should IDs be UUIDs or simple sequential numbers?