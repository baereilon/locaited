# Verifier Agent Implementation Tasks

**Feature Branch:** `feature/verifier-agent`  
**PRD:** [PRD-005](prd_005_verifier_agent.md)  
**Start Date:** August 21, 2025  
**Target Completion:** August 28, 2025  

## Phase 1: Extract Current Logic

### 1. Analysis & Documentation (Day 1)
- [ ] 1.1 Document current Researcher validation logic flow
- [ ] 1.2 Identify all validation-related methods in Researcher
- [ ] 1.3 Map data structures passed between validation steps
- [ ] 1.4 Create `docs/AGENTS.md` with current responsibilities

### 2. Create Verifier Agent Structure (Day 1-2)
- [ ] 2.1 Create `locaited/agents/verifier.py` with BaseAgent inheritance
- [ ] 2.2 Define Verifier input/output data structures
- [ ] 2.3 Create abstract interface that both implementations will follow
- [ ] 2.4 Add caching mechanism for decisions

### 3. Implement Option A: LLM-Based (Day 2)
- [ ] 3.1 Implement `VerifierLLM` class
- [ ] 3.2 Create prompt for specificity/temporality classification
- [ ] 3.3 Add JSON schema for structured output
- [ ] 3.4 Test LLM implementation standalone

### 4. Implement Option B: LlamaIndex-Based (Day 2-3)
- [ ] 4.1 Install LlamaIndex dependencies
- [ ] 4.2 Implement `VerifierLlamaIndex` class
- [ ] 4.3 Create document examples for specificity patterns
- [ ] 4.4 Create document examples for temporality patterns
- [ ] 4.5 Implement embedding-based similarity matching
- [ ] 4.6 Test LlamaIndex implementation standalone
- [ ] 4.7 Ensure output format matches Option A exactly

### 5. Extract Logic from Researcher (Day 3)
- [ ] 5.1 Move validation prompt logic to Verifier
- [ ] 5.2 Remove validation methods from Researcher
- [ ] 5.3 Update Researcher to handle Verifier feedback
- [ ] 5.4 Reorder Researcher flow: generate → reality → refine → expand

### 6. Workflow Integration (Day 4)
- [ ] 6.1 Add Verifier node to workflow graph
- [ ] 6.2 Add configuration flag to choose implementation (LLM vs LlamaIndex)
- [ ] 6.3 Implement conditional edge: Researcher → Verifier
- [ ] 6.4 Implement conditional edge: Verifier → Researcher/Fact-Checker
- [ ] 6.5 Add iteration counter and limits

### 7. Testing & Validation (Day 4-5)
- [ ] 7.1 Write unit tests for VerifierLLM (V6)
- [ ] 7.2 Write unit tests for VerifierLlamaIndex (V7)
- [ ] 7.3 Write tests for both implementations (V5, V8, V9, V1-alt, V2-alt)
- [ ] 7.4 Write unit tests for updated Researcher (R2, R3, R4a, R4b)
- [ ] 7.5 Write integration tests for cycle (I1, I2, I3)
- [ ] 7.6 Run A/B comparison test between implementations

### 8. Debug & Refinement (Day 5)
- [ ] 8.1 Fix any breaking changes
- [ ] 8.2 Ensure debug mode shows Verifier steps
- [ ] 8.3 Verify caching works correctly for both implementations
- [ ] 8.4 Performance testing (should not add >2 seconds)
- [ ] 8.5 Cost comparison between implementations

## Definition of Done

- [ ] Verifier agent created with both LLM and LlamaIndex implementations
- [ ] Researcher refactored to use Verifier
- [ ] All existing tests still passing
- [ ] All new tests passing
- [ ] Same output quality as current system
- [ ] Documentation updated
- [ ] A/B test results documented

## Progress Tracking

| Task Group | Status | Completion Date | Notes |
|------------|--------|-----------------|-------|
| 1. Analysis & Documentation | Not Started | - | |
| 2. Create Verifier Structure | Not Started | - | |
| 3. Implement Option A (LLM) | Not Started | - | |
| 4. Implement Option B (LlamaIndex) | Not Started | - | |
| 5. Extract Logic from Researcher | Not Started | - | |
| 6. Workflow Integration | Not Started | - | |
| 7. Testing & Validation | Not Started | - | |
| 8. Debug & Refinement | Not Started | - | |

## Dependencies

- Current Researcher implementation
- Workflow graph structure
- Existing test infrastructure
- LlamaIndex library

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing functionality | High | Comprehensive testing before/after |
| State management in cycles | Medium | Clear state documentation |
| Cache key conflicts | Low | Namespace cache keys |
| LlamaIndex learning curve | Medium | Start with simple patterns |

## Notes

- Keep both implementations behind feature flag for easy switching
- Ensure identical output format between LLM and LlamaIndex
- Monitor performance impact closely
- Document any deviations from PRD