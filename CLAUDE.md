# LocAIted Project Context for Claude

## Product Overview
LocAIted is a multi-agent system that helps photojournalists discover newsworthy events in NYC. It automates the process of finding, verifying, and curating events that are worth photographing, saving journalists hours of manual research.

## User Flow
1. **User Input**: Photojournalist specifies interests (e.g., "protests and cultural events in Brooklyn this week")
2. **Profile Building**: Editor creates a comprehensive search profile with guidance
3. **Lead Generation**: Researcher generates 25+ specific event leads using LLM
4. **Evidence Gathering**: Fact-Checker searches for evidence of each lead using Tavily
5. **Event Extraction**: Publisher extracts concrete events from evidence
6. **Quality Gate**: Publisher decides if enough quality events found (APPROVE) or need retry (RETRY)
7. **Feedback Loop**: If RETRY, Editor adjusts strategy based on feedback
8. **Final Output**: Curated list of 5-10 verified events with details (date, time, location, access requirements)

## Agent Goals and Responsibilities

### Editor Agent (LLM-based)
- **Goal**: Understand user intent and create actionable search profiles
- **LLM Calls**: 
  - One call to build/refine profile based on user input and feedback
  - Uses complete_json() to get structured profile
- **Responsibilities**:
  - Parse user input (location, timeframe, interests)
  - Generate researcher guidance for better leads
  - Handle Publisher feedback on retries
  - Track iteration count (max 3 retries)
- **Key Output**: Profile with location, interests, and specific researcher_guidance

### Researcher Agent (LLM-based)
- **Goal**: Generate specific, searchable event leads
- **LLM Calls**:
  - One call to generate 25 event leads
  - Uses complete_json() to get structured event list
- **Responsibilities**:
  - Use LLM to generate 25 diverse event leads
  - Create specific descriptions (not generic)
  - Include searchable keywords and organizations
  - Consider seasonal and current events context
- **Key Output**: List of leads with descriptions, types, and search queries

### Fact-Checker Agent (API-based, no LLM)
- **Goal**: Find evidence for event leads while managing API costs
- **External Calls**:
  - Tavily API for web searches (5-8 searches max per run)
  - No LLM calls - pure API wrapper
- **Responsibilities**:
  - Search for evidence using Tavily API
  - Implement smart batching (5-8 searches max)
  - Cache results to avoid duplicate searches
  - Extract relevant information from search results
- **Key Output**: Evidence list with search results and extracted answers

### Publisher Agent (LLM-based)
- **Goal**: Extract real events and ensure quality
- **LLM Calls**:
  - First call: Extract and deduplicate events from evidence
  - Second call: Make gate decision and score events
  - Both use complete_json() for structured output
- **Responsibilities**:
  - Extract concrete events from evidence using LLM
  - Deduplicate similar events
  - Score events (0-100) on photographic potential
  - Make gate decision (APPROVE if 5+ quality events)
  - Provide actionable feedback for retries
- **Key Output**: Final events list or retry feedback

## Core Development Principles

### Budget Awareness
- **Tavily API**: Limited credits, use caching aggressively
- **OpenAI API**: Small cap, optimize prompts for efficiency
- **Strategy**: Cache everything, batch operations, avoid redundant calls
- **Cost tracking**: Every agent tracks and reports costs

### Caching & Deduplication
- **File-based caching**: Organized by version/agent/query
- **Cache keys**: Based on location + timeframe
- **Deduplication**: Publisher removes duplicate events
- **Smart batching**: Fact-Checker limits searches to 5-8

### Benchmarking
- **Test data**: "Liri Interesting events.csv" with pre-approved events
- **Success metrics**: 
  - Precision: How many found events are actually interesting?
  - Recall: How many interesting events were found?
  - Cost efficiency: Total API cost per successful run

### Iterative Development
- **Small steps**: Test each agent individually first
- **Frequent check-ins**: Run test_workflow_v4.py after each change
- **Version control**: Clear v0.4.0 naming, git tags
- **Debugging**: Comprehensive logging at each step

## Assessment Principles
The project will be assessed based on:

### Functionality
- Agents coordinate effectively through LangGraph
- Retry logic works with feedback propagation
- Events are successfully found and extracted
- Gate decisions are reasonable and well-justified

### Code Quality
- Clean, modular architecture
- Proper error handling and logging
- Consistent naming conventions
- Effective use of inheritance (BaseAgent, CachedAgent)
- Well-organized file structure

### Documentation & Demo
- Clear README with setup instructions
- Architecture diagrams and flow documentation
- Easy installation process
- Working demo with sample outputs
- Comments where complex logic requires explanation

## Technical Configuration

### Environment Management
**IMPORTANT**: Always use `micromamba run -n locaited` to execute Python scripts.

```bash
# Run tests
micromamba run -n locaited python test_workflow_v4.py

# Run any Python script
micromamba run -n locaited python script.py

# Install packages
micromamba run -n locaited pip install package_name
```

### API Configuration
- **Model**: gpt-4.1-mini (NOT gpt-5-mini or gpt-4o-mini)
- **Temperature**: 1.0 (only supported value)
- **Max tokens**: Use max_completion_tokens parameter
- **API keys**: Stored in .env.secret (auto-loaded by micromamba)

### Testing Commands
```bash
# Main workflow test
micromamba run -n locaited python test_workflow_v4.py

# Individual agent tests (when available)
micromamba run -n locaited python test_editor.py
micromamba run -n locaited python test_researcher.py

# Linting and type checking (to be added)
micromamba run -n locaited ruff check .
micromamba run -n locaited mypy .
```

## Key Files Structure
```
locaited/
├── environment.yml          # Micromamba environment definition
├── .env.secret             # API keys (gitignored)
├── test_workflow_v4.py     # Main test script
├── src/
│   ├── agents/
│   │   ├── base_agent.py      # Base classes with caching
│   │   ├── editor_v4.py       # Profile builder (LLM-based)
│   │   ├── researcher_v4.py   # Lead generator (LLM-based)
│   │   ├── fact_checker_v4.py # Evidence gatherer (Tavily API)
│   │   ├── publisher_v4.py    # Event extractor (LLM-based)
│   │   └── workflow_v4.py     # LangGraph orchestration
│   └── utils/
│       ├── llm_client.py      # OpenAI wrapper with cost tracking
│       └── tavily_client.py   # Tavily wrapper with caching
└── cache/
    └── v0.4.0/                # Version-specific cache
        ├── researcher/
        ├── fact_checker/
        └── publisher/
```

## Current Status
- v0.4.0 core implementation complete
- Micromamba environment working
- Model updated to gpt-4.1-mini
- Testing workflow for end-to-end validation

## Next Steps
1. Complete workflow testing
2. Add benchmark evaluation against test data
3. Optimize API usage based on metrics
4. Document setup process in README
5. Create demo video/screenshots