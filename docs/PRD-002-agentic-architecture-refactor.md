# PRD: Agentic Architecture Refactor

## Overview
Refactor the current multi-agent pipeline into a clean two-agent system (Scout + Editor) with iterative feedback loops, replacing the existing Editor/Researcher/Fact-Checker/Publisher architecture.

## Goals
- **Clean Architecture**: New files, minimal legacy code preservation
- **Iterative Refinement**: Scout and Editor collaborate until quality threshold met
- **Enhanced Visibility**: Full debug mode support for all agent interactions
- **Maintainable State**: Clear data models for run state and event tracking

## Core Architecture

### Two-Agent System
1. **Scout Agent**: Profile creation, search query generation, event discovery via Tavily, URL enrichment
2. **Editor Agent**: Event validation, profile matching, quality control, iteration decisions

### LangGraph Orchestration
- Scout ↔ Editor iteration loop until completion criteria met
- Maximum iterations configurable (default: 3)
- Full debug visibility for node transitions and tool calls

## Data Models

### RunState Schema
```
- approved_events: List[Event]
- pending_events: List[Event]
- rejected_events: List[Event]
- refinement_instructions: str (e.g., "need more fashion events")
- profile: UserProfile
- iteration_count: int
```

### Event Schema (Enhanced)
```
- [existing fields]: title, date, time, location, score, access_requirement
- source_url: str
- refinement_instructions: str (event-specific feedback)
- status: enum(approved, pending, rejected)
```

## Agent Responsibilities

### Scout Agent
- **Profile Creation**: One-time user input → structured profile
- **Query Generation**: Profile + refinement instructions → search queries
- **Event Discovery**: Tavily searches → parsed event leads
- **URL Enrichment**: Tool to find/improve source URLs for events
- **Event Refinement**: Address specific Editor feedback (fix URLs, add details)

### Editor Agent
- **Validation**: Timeframe compliance, specificity, factual accuracy
- **Profile Matching**: Events alignment with user profile
- **Quality Control**: Deduplication, completeness checks
- **Iteration Decisions**: Approve final batch vs. request more events
- **Feedback Generation**: Specific instructions for Scout improvements

## Completion Criteria
- **Primary**: Events adequately answer user request (number + diversity)
- **Minimum**: 3 approved events (configurable)
- **Fallback**: Maximum iterations reached

## Technical Requirements

### External Interface
- **API Compatibility**: Maintain existing `/workflow/discover` endpoint structure to minimize breaking changes
- **Incremental UI Evolution**: Allow UI to be updated progressively to show new agent interactions
- **Enhanced Debug Output**: Expand debug mode data to include Scout/Editor iterations and state transitions
- **Configuration Exposure**: New agent settings (iteration limits, minimum events) available to UI

### State Management
- In-memory RunState persistence during workflow
- Event-level refinement tracking
- Cumulative approved events across iterations

### Configuration
- Centralized config in existing `src/config.py`
- Iteration limits, minimum events, debug settings

### Debug Mode
- Full visibility: agent states, tool calls, decisions
- Track iteration progression and feedback loops
- Event status transitions and refinement attempts

## Success Metrics
- Clean, maintainable codebase with minimal legacy dependencies
- Functional Scout ↔ Editor iteration loop
- Preserved external API compatibility
- Enhanced debug visibility throughout pipeline