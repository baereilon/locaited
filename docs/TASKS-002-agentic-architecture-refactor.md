# Sub-Tasks: Agentic Architecture Refactor

Based on PRD-002, this document outlines the implementation tasks for refactoring to a Scout + Editor agent system.

## Phase 1: Foundation & Setup

### Task 1.1: Study Existing LangGraph Implementation
- Analyze current `locaited/agents/workflow.py` patterns
- Document state management approach
- Identify reusable patterns for new workflow

### Task 1.2: Create New Data Models
- Create `locaited/models/` directory
- Implement `RunState` schema with approved/pending/rejected events
- Enhance `Event` schema with refinement_instructions and status fields
- Define state transition enums and validation

### Task 1.3: Move Legacy Agents
- Create `locaited/agents/legacy/` directory
- Move existing agents (editor, researcher, fact_checker, publisher) to legacy
- Update import paths where needed for compatibility

### Task 1.4: Update Configuration
- Add iteration limits (default: 3) to `config.py`
- Add minimum events setting (default: 3) to `config.py`
- Add debug mode settings for new agent system

## Phase 2: Core Agent Implementation

### Task 2.1: Implement Scout Agent - Profile Creation
- Create `locaited/agents/scout.py`
- Implement profile creation from user input
- Handle ExtendedSearchRequest → UserProfile conversion

### Task 2.2: Implement Scout Agent - Query Generation
- Add query generation logic based on profile
- Handle refinement instructions input for subsequent iterations
- Generate diverse search queries for Tavily

### Task 2.3: Implement Scout Agent - Tavily Integration
- Implement Tavily as a tool within Scout (not separate agent)
- Add event parsing from search results
- Handle search result → Event conversion

### Task 2.4: Implement Editor Agent - Validation Logic
- Create `locaited/agents/editor.py`
- Implement timeframe compliance validation
- Add specificity and factual accuracy checks

### Task 2.5: Implement Editor Agent - Profile Matching
- Add logic to match events against user profile
- Implement profile alignment scoring
- Handle event filtering based on profile fit

### Task 2.6: Implement Editor Agent - Completion Criteria
- Add logic to evaluate if events adequately answer user request
- Implement diversity and quantity assessment
- Create decision logic for approve vs. iterate

## Phase 3: Agent Orchestration

### Task 3.1: Create New LangGraph Workflow
- Create `locaited/agents/workflow_v2.py`
- Implement Scout ↔ Editor iteration loop
- Handle state transitions and iteration counting

### Task 3.2: Implement Event Status Management
- Add event status transition logic (pending → approved/rejected)
- Implement cumulative event tracking across iterations
- Handle event state persistence during workflow

### Task 3.3: Create Initial Integration Test
- Create basic end-to-end workflow test
- Verify Scout → Editor → completion flow
- Test with simple user input scenario

## Phase 4: Refinement Instructions System

### Task 4.1: Implement RunState Refinement Instructions
- Add creation logic for workflow-level refinement instructions
- Implement instruction persistence in RunState
- Handle instruction updates between iterations

### Task 4.2: Implement EventState Refinement Instructions
- Add event-level refinement instruction tracking
- Implement event-specific feedback storage
- Handle refinement instruction updates per event

### Task 4.3: Create Scout Refinement Interpretation
- Add logic for Scout to read and act on RunState refinement instructions
- Implement event-level refinement instruction processing
- Handle query modification based on feedback

### Task 4.4: Create Editor Refinement Generation
- Add logic for Editor to generate specific, actionable feedback
- Implement RunState refinement instruction creation
- Add event-level refinement instruction generation

## Phase 5: Advanced Features

### Task 5.1: Migrate API Endpoint
- Update `/workflow/discover` to use new agent system
- Maintain existing request/response compatibility
- Preserve external API contract

### Task 5.2: Implement URL Enrichment Tool
- Add URL lookup tool within Scout agent
- Handle broken/missing URL discovery
- Integrate with event refinement instructions

### Task 5.3: Add Event Refinement Logic
- Implement Scout logic to fix specific event issues
- Handle URL replacement, detail enhancement
- Process event-level refinement instructions

### Task 5.4: Implement Deduplication Logic
- Add deduplication logic to Editor agent
- Implement event similarity detection
- Handle duplicate removal and merging

## Phase 6: Debug Mode Enhancement

### Task 6.1: Design Debug Output Schema
- Define debug data structure for new agent system
- Plan iteration tracking and state transition logging
- Design agent operation visibility format

### Task 6.2: Implement Scout Debug Tracking
- Add debug output for profile creation
- Track query generation and Tavily searches
- Log event parsing and refinement operations

### Task 6.3: Implement Editor Debug Tracking
- Add debug output for validation processes
- Track profile matching and completion decisions
- Log refinement instruction generation

### Task 6.4: Implement Workflow Debug Tracking
- Add iteration loop visibility
- Track state transitions and event status changes
- Log workflow completion criteria evaluation

### Task 6.5: Create Debug Output Formatters
- Update debug formatters for new agent outputs
- Handle new state structure formatting
- Integrate with existing debug display system

## Phase 7: Testing & Validation

### Task 7.1: Create Scout Agent Unit Tests
- Test profile creation functionality
- Test query generation and Tavily integration
- Test event parsing and refinement logic

### Task 7.2: Create Editor Agent Unit Tests
- Test validation logic (timeframe, specificity, factual accuracy)
- Test profile matching and completion criteria
- Test refinement instruction generation

### Task 7.3: Create Refinement Instructions System Tests
- Test RunState refinement instruction flow
- Test event-level refinement instruction handling
- Test Scout interpretation and Editor generation

### Task 7.4: Create Comprehensive Workflow Tests
- Test multi-iteration scenarios
- Test various completion criteria paths
- Test error handling and edge cases

### Task 7.5: Performance Testing and Optimization
- Test iteration loop performance
- Optimize token usage and API calls
- Validate against cost targets (<$0.05 per run)

## Phase 8: Cleanup

### Task 8.1: Clean Up Legacy Code
- Remove legacy agent files from `locaited/agents/legacy/`
- Clean up unused imports and dependencies
- Remove obsolete configuration settings

### Task 8.2: Final Documentation and Validation
- Update system documentation
- Verify all PRD requirements met
- Conduct final integration testing