# LocAIted Testing Infrastructure

## Test Structure

The testing infrastructure is organized into two main categories:

### Unit Tests (`tests/unit/`)
Tests individual agent functionality in isolation:

- **`test_agent_editor_creates_profile.py`** (5 tests)
  - Profile creation from user input
  - Retry handling with feedback
  - Context formatting
  - String input handling
  - Cost tracking

- **`test_agent_researcher_generates_leads.py`** (6 tests)
  - Searchable query generation
  - Date constraint enforcement
  - Editor guidance usage
  - Event categorization
  - Cost tracking
  - Timeframe handling

- **`test_agent_fact_checker_gathers_evidence.py`** (7 tests)
  - Lead searching
  - Tavily caching
  - Evidence extraction
  - API cost tracking
  - No results handling
  - Error handling
  - Batch processing

- **`test_agent_publisher_extracts_events.py`** (8 tests)
  - Event extraction from evidence
  - Event deduplication
  - Event scoring
  - Gate decisions (APPROVE/RETRY)
  - 15-event limit enforcement
  - Retry feedback generation
  - LLM cost tracking
  - No evidence handling

### Integration Tests (`tests/integration/`)
Tests coordination between agents:

- **`test_workflow_coordination.py`** (5 tests)
  - Editor → Researcher handoff
  - Researcher → Fact-Checker handoff
  - Fact-Checker → Publisher handoff
  - Publisher RETRY → Editor feedback loop
  - Full pipeline flow

## Test Configuration

### `conftest.py`
Central pytest configuration with:
- Session-scoped mock fixtures for LLMClient and TavilyClient
- Custom test markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
- Shared test data and utilities

### `pytest.ini`
- Test discovery patterns
- Marker definitions
- Coverage configuration

## Running Tests

```bash
# Run all tests
micromamba run -n locaited pytest

# Run only unit tests
micromamba run -n locaited pytest tests/unit/ -v

# Run only integration tests
micromamba run -n locaited pytest tests/integration/ -v

# Run specific test file
micromamba run -n locaited pytest tests/unit/test_agent_editor_creates_profile.py -v

# Run with coverage
micromamba run -n locaited pytest --cov=src --cov-report=html

# Run marked tests
micromamba run -n locaited pytest -m unit
micromamba run -n locaited pytest -m integration
```

## Key Testing Patterns

### Mocking Strategy
- Mock at the wrapper level (LLMClient, TavilyClient) not the underlying libraries
- Disable caching in test fixtures to ensure mocks are called
- Use MagicMock for complex objects with attributes

### Common Issues and Solutions
1. **Cache interference**: Disable caching with `agent.use_cache = False`
2. **Mock not called**: Check if caching is enabled
3. **Field name mismatches**: Verify actual implementation field names
4. **Missing mock attributes**: Add required attributes to MagicMock

## Test Coverage Goals
- Unit tests: Core functionality of each agent
- Integration tests: Agent coordination and data flow
- Error handling: Graceful failure modes
- Edge cases: Empty inputs, API failures, retry logic

## Future Enhancements
- [ ] Schema validation tests for JSON outputs
- [ ] Error handling and retry logic tests
- [ ] Performance benchmark tests
- [ ] API smoke tests with real connectivity
- [ ] Coverage reporting with 80%+ target