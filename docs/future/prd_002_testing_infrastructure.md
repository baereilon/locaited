# PRD: Testing Infrastructure for LocAIted

## Problem
The project has minimal testing with only 5 test cases, no unit tests, and tests that make expensive API calls. This makes development risky and expensive.

## Goal
Build a robust testing infrastructure that enables confident development without API costs.

## Success Metrics
- 80%+ code coverage for critical paths
- Zero API costs during test runs
- Test suite runs in <30 seconds
- All agents have unit tests

## Proposed Solution

### Phase 1: Test Structure & Organization
Create proper test hierarchy with clear separation of concerns:
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests
├── fixtures/       # Shared test data
└── conftest.py     # Pytest configuration
```

### Phase 2: Unit Tests with Mocking
Extract and refactor existing agent tests from `if __name__ == "__main__"` blocks into proper unit tests. Mock all external dependencies:
- OpenAI API calls → Return pre-recorded responses
- Tavily API calls → Return cached search results
- File I/O → Use temporary directories

### Phase 3: Test Fixtures & Utilities
Create reusable test components:
- Sample user inputs (location, timeframe, interests)
- Mock API responses for common scenarios
- Expected agent outputs for validation
- Helper functions for assertion patterns

### Phase 4: Integration Tests
Test agent interactions without external APIs:
- Editor → Researcher flow
- Researcher → Fact-Checker flow
- Fact-Checker → Publisher flow
- Complete workflow with retry logic

### Phase 5: Performance & Validation
Add specialized test suites:
- Schema validation for all JSON outputs
- Date constraint verification
- Deduplication algorithm tests
- Cost calculation accuracy
- Performance benchmarks (memory, speed)

## Implementation Approach

### Immediate Actions (Week 1)
1. **Create test structure** - Set up directories and pytest config
2. **Extract unit tests** - Convert existing agent test code
3. **Mock external APIs** - Create fixtures for OpenAI/Tavily responses
4. **Add basic assertions** - Replace print statements with proper checks

### Medium-term Actions (Week 2)
1. **Integration tests** - Test agent coordination
2. **Schema validation** - Verify JSON structures
3. **Error path testing** - Test retry logic and error handling
4. **Performance baselines** - Establish speed/memory benchmarks

## Technical Decisions

### Testing Stack
- **pytest** - Test framework (already installed)
- **pytest-mock** - Mocking support
- **pytest-cov** - Coverage reporting
- **responses** - HTTP response mocking
- **freezegun** - Time/date mocking

### Mocking Strategy
- Use recorded real API responses as fixtures
- Create "golden" test cases from successful runs
- Mock at the client level, not HTTP level
- Maintain separate fixture sets for different scenarios

### Coverage Goals
- Critical: 90%+ (workflow, agents)
- Important: 80%+ (utilities, clients)
- Nice-to-have: 60%+ (CLI, logging)

## Risks & Mitigations
- **Risk**: Tests become brittle with mocking
  - **Mitigation**: Mock at appropriate abstraction level
- **Risk**: Fixture maintenance overhead
  - **Mitigation**: Use recorded responses, update quarterly
- **Risk**: Tests don't catch real API changes
  - **Mitigation**: Keep one smoke test for real APIs (manual run)

## Out of Scope
- CI/CD setup (future PRD)
- E2E browser testing
- Load/stress testing
- Security testing

## Questions for Discussion
1. Should we use VCR.py for recording/replaying HTTP interactions?
2. What's our stance on testing private methods?
3. Should benchmark tests run by default or only on-demand?
4. Do we need contract tests for API schemas?