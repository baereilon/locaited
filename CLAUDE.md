# Claude Context for LocAIted

## User Interface & Flow (v1.0)

### Single-Flow Architecture
**IMPORTANT**: The UI implements a single-flow design where users provide profile + query in one form submission.
See `docs/USER-FLOW-V1.md` for complete specification.

**Key Points:**
- Endpoint: `POST /workflow/discover` (uses ExtendedSearchRequest)
- No authentication or user persistence
- TIME field is CRITICAL - must be extracted and displayed prominently
- Returns max 15 events to prevent JSON overflow
- Frontend at `locaited-ui/` built with React + Material-UI

**Backend Must Preserve:**
- All required fields (title, date, time, location)
- Score range (0-100)
- Access requirement values (public_only, press_pass, vip_access)
- The `/workflow/discover` endpoint contract

## AI Dev Tasks Protocol

### Core Workflow for Development Tasks
1. **PRD Creation** - Define feature scope, purpose, and requirements
2. **Task List Generation** - Break PRD into granular, step-by-step tasks
3. **Review & Approval** - Present tasks to user for approval BEFORE starting
4. **Iterative Implementation** - One task at a time with verification

### Key Principles
- **Never start implementation without approval**
- **Focus on one task at a time**
- **Get feedback before moving to next task**
- **Maintain clear checkpoints for verification**

### Process Steps
1. When user requests a feature → Create PRD
2. After PRD approval → Generate detailed task list
3. After task list approval → Begin implementation
4. After each task → Verify and get approval for next

## Critical Reminders

### Execution
- **ALWAYS** use `micromamba run -n locaited python` for any Python execution
- Never use plain `python` - environment won't load properly

### North Star Metrics (What We Measure)
1. **# Interesting Events** - Manually assessed by user
2. **# Events with Complete Info** - Must have title, date, TIME, location
3. **# Duplicate Events** - Should be minimal after Publisher dedup

**CRITICAL**: Publisher must return ALL unique extracted events for validation, not just top 10 scored

### Known Issues to Remember
- **Times not extracting**: Publisher extracts dates but misses times from evidence
- **Date constraints weak**: Researcher generates past events for future queries (June events for August "this week")
- **Temperature**: gpt-4.1-mini ONLY supports 1.0, will error on any other value
- **max_tokens**: Must use `max_completion_tokens` not `max_tokens` in API calls

## Development Principles

### When Making Changes
1. Test with `validate_workflow.py` - generates CSVs for manual review
2. Check benchmarks/results/v0.4.0/ for outputs
3. Small iterative changes with frequent testing
4. If user says something is elegant/efficient, don't over-engineer

### Cost Management
- Tavily: ~$0.025 per workflow (25 searches)
- OpenAI: ~$0.006 per workflow
- Total target: <$0.05 per run
- Cache aggressively - we have limited API credits

### LLM vs Code Solutions
- **Use LLM for**: Text processing, extraction, decisions
- **Use code for**: Routing, caching, file operations
- When in doubt, prefer LLM solutions

## Recent Decisions & Context

### Why Micromamba
- Replaced venv due to repeated .env loading issues
- Auto-loads .env.secret on activation
- More reliable than pip venv

### Publisher Output Limit
- Limited to 15 events max to prevent JSON parsing errors
- Was getting 24k+ tokens causing truncation
- Gate decision based on top 10 scored events

### Agent Tracking
- Using Option 1: Best-effort matching with existing data
- PRD-001 in docs/future/ for proper tracking implementation
- No code changes needed for now

### File Organization
- Consolidated test files to just 3: test_api_connection, test_workflow, benchmark_workflow
- Validation outputs go in benchmarks/results/v0.4.0/
- Using CSV format to match v0.3.0 for consistency

## Gotchas to Avoid

### API Parameters
- `complete_json()` for structured output, not `complete()`
- Include `temperature=1.0` explicitly
- Use `max_completion_tokens` not `max_tokens`

### Testing
- `validate_workflow.py` is the main validation tool
- Outputs CSVs not JSON for manual review
- Always check agent_outputs CSV for pipeline visibility

### Git Hygiene
- Don't create new test files - consolidate
- Keep temporary files out of git
- Update existing files rather than creating new ones

## What Each Agent Actually Does

### Editor
- ONE LLM call to create profile
- Handles retry feedback from Publisher

### Researcher  
- ONE LLM call to generate 25 leads
- Should enforce date constraints (currently weak)

### Fact-Checker
- NO LLM calls - pure Tavily API
- Searches all 25 leads (not limited to 5-8 despite docs)
- Heavy caching to avoid duplicate searches

### Publisher
- TWO LLM calls: extract events, then gate decision
- Deduplicates and scores events
- Returns max 15 to prevent JSON overflow

## Current State Notes
- Test files cleaned up and consolidated
- Config centralized in src/config.py
- CSVs properly generated in benchmarks/results/v0.4.0/
- Critical files now in git (validate_workflow.py, docs/)
- Report back means I want you to share with what you plan on doing so I can approve it before you actually do it. eg Report back with a documenation of X means send me the proposed documentation to review before creating the actual file
- Do not run to implement tasks/fixes without me telling you to do so
- Do not add Claude signature to Git commits