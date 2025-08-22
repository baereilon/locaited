# PRD-005: Event Verifier Agent

**Author:** System Architecture Team  
**Date:** August 21, 2025  
**Status:** Approved  
**Priority:** High  
**Estimated Effort:** 5-7 days  

## 1. Problem Statement

The Researcher agent currently handles too many responsibilities, making it difficult to:
- Test and improve individual capabilities
- Understand where quality issues originate
- A/B test different verification approaches

Specifically, the validation of event specificity and temporality is buried within the Researcher, making it impossible to compare LLM-based vs LlamaIndex-based approaches.

## 2. Agent Responsibilities - Clear Definition

### Editor Agent
**Purpose:** Transform user input into actionable search profile  
**Responsibilities:**
- Parse user query and interests
- Generate search keywords and domains
- Handle retry feedback from Publisher
- Create researcher guidance

**Does NOT:** Generate events, verify events

### Researcher Agent
**Purpose:** Generate high-quality event leads  
**Responsibilities:**
1. **Generate** initial event ideas (50 events)
2. **Reality Check** - Filter hallucinated events (REAL vs FAKE venues/orgs)
3. **Refine** based on Verifier feedback (if second+ iteration)
4. **Expand** generic events into specific sub-events

**Does NOT:** Validate dates/specificity, extract from evidence

### Verifier Agent (NEW)
**Purpose:** Validate event specificity and temporality  
**Responsibilities:**
1. **Specificity Check** - Has concrete date AND location? (time is bonus)
2. **Temporality Check** - Is it future, past, or ongoing?

**Does NOT:** Generate events, check if venues exist, search web, filter events, provide suggestions

### Fact-Checker Agent
**Purpose:** Find web evidence for events  
**Responsibilities:**
- Search Tavily for each lead
- Cache results aggressively
- Extract relevant snippets
- Track search costs

**Does NOT:** Generate events, validate events, extract structured data

### Publisher Agent
**Purpose:** Extract and curate final events  
**Responsibilities:**
1. **Extract** structured events from evidence
2. **Reality Check** (second pass using evidence)
3. **Deduplicate** similar events
4. **Score** events for quality
5. **Gate Decision** - Accept/Retry/Reject

*Future Note: Consider splitting into Extractor (1-2) and Curator (3-5)*

**Does NOT:** Generate new events, search web

## 3. Workflow Architecture

```
Proposed Flow with Two Cycles:

Editor → Researcher ↔ Verifier → Fact-Checker → Publisher
         ↑                                          ↓
         └────────── (existing cycle) ──────────────┘
         
Where:
- Verifier → Researcher: If <15 specific+future events (max 3 iterations)
- Publisher → Researcher: If quality gate fails (existing behavior)
```

## 4. Verifier Agent Specification

### Core Functions

**Input:** List of event descriptions from Researcher  
**Output:** Pass/fail for each event on two criteria

**Verification Criteria:**
1. **Specificity**
   - SPECIFIC: Has date AND location (time is bonus, not required)
   - GENERIC: Missing date OR location
   
2. **Temporality**
   - FUTURE: Happening after today
   - PAST: Already occurred
   - ONGOING: Happening now/this week
   - UNCLEAR: No temporal markers

### Implementation Options

**Option A: LLM-Based (using GPT-3.5)**
- Direct prompt asking for classification
- Structured JSON output
- ~$0.001 per batch of 10 events

**Option B: LlamaIndex-Based**
- Pattern matching against example documents
- Embedding similarity search
- ~$0.0001 for embeddings + local compute

Both implementations will:
- Expose identical interface
- Return same output format
- Support caching of decisions

## 5. Cyclic Refinement Process

### Verifier → Researcher Cycle
1. **Researcher** generates 50 events
2. **Researcher** does reality check (removes fake venues)
3. **Verifier** validates all remaining events
4. **Decision Point:**
   - If ≥15 events are BOTH specific AND future → continue to Fact-Checker
   - If <15 events pass AND iterations <3 → back to Researcher
   - If iterations ≥3 → continue with what we have

### Publisher → Researcher Cycle (Existing)
- Maintains current behavior
- Publisher can request retry with feedback
- Editor processes feedback and updates profile

## 6. Success Metrics

### Verifier Accuracy (Primary)
- **True Positive Rate**: Correctly identifies specific+future events
- **True Negative Rate**: Correctly rejects generic/past events
- **Agreement with Manual**: >85% match with human validation

### System Impact (Secondary)
- **Lead Quality**: 20% increase in events with date AND location
- **Fact-Checker Efficiency**: 15% fewer failed searches
- **Iteration Count**: Average 1.5 cycles to get 15+ good events

## 7. Testing Methodology

### Unit Tests

**Researcher Tests**
- R2: `test_researcher_reality_check_removes_fake_venues()`
- R3: `test_researcher_receives_verifier_feedback()`
- R4a: `test_researcher_calls_expansion_for_generic_events()`
- R4b: `test_researcher_handles_expansion_results()`

**Verifier Tests**
- V5: `test_verifier_caches_decisions()`
- V6: `test_verifier_llm_implementation()`
- V7: `test_verifier_llamaindex_implementation()`
- V8: `test_verifier_output_format_consistency()`
- V9: `test_verifier_processes_all_events()`
- V1-alt: `test_verifier_contract()`
- V2-alt: `test_verifier_handles_edge_cases()`

**Integration Tests**
- I1: `test_researcher_verifier_cycle()`
- I2: `test_max_iterations_respected()`
- I3: `test_cache_used_in_cycles()`

### A/B Test Design
```
Group A: LLM-based Verifier
Group B: LlamaIndex-based Verifier
Sample: 20 identical queries

Measurement:
1. Accuracy (vs manual validation)
2. Speed (seconds per verification)
3. Cost (per 100 events)
4. Final event quality
```

### Validation Process
1. Run both verifiers on same Researcher output
2. Export results to CSV:
   - Event description
   - Verifier_A_specific (T/F)
   - Verifier_A_temporal (FUTURE/PAST/ONGOING/UNCLEAR)
   - Verifier_B_specific (T/F)
   - Verifier_B_temporal (FUTURE/PAST/ONGOING/UNCLEAR)
   - Manual_specific (human fills)
   - Manual_temporal (human fills)
3. Calculate accuracy metrics
4. Choose winning approach

## 8. Documentation Strategy

Create `docs/AGENTS.md` with:
- Clear purpose for each agent
- Detailed responsibilities
- What each agent does NOT do
- Data flow between agents
- Decision points in workflow
- Cyclic processes explained

Main README.md will link to this detailed documentation.

## 9. Implementation Phases

**Phase 1: Extract Current Logic**
- Move validation logic from Researcher to Verifier
- Keep reality check in Researcher
- Update Researcher's process order (refine → expand)
- Test that results match current system

**Phase 2: Add LlamaIndex Option**
- Implement pattern-based verification
- Create example documents for date/location patterns
- Ensure same output format as LLM

**Phase 3: Unit Testing**
- Write comprehensive unit tests for both agents
- Test edge cases (no events, all pass, all fail)
- Test cycle limits

**Phase 4: A/B Testing**
- Run both implementations on same data
- Collect metrics
- Manual validation
- Choose winner

**Phase 5: Documentation**
- Update agent responsibility docs
- Add to workflow diagram
- Update README

## 10. Decisions Made

| Decision | Rationale |
|----------|-----------|
| Time not required for specificity | Many good events don't have exact times |
| Verifier doesn't provide suggestions | Keep it simple, just classify |
| Cache Verifier decisions | Avoid re-verifying identical events |
| Verify all events | Don't miss potential good events |
| Max 3 iterations | Prevent infinite loops |
| Separate branch for development | Keep master stable for review |