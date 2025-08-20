# PRD: Micromamba Implementation for LocAIted

## Overview
Replace the current Python venv + .env file setup with Micromamba for better environment and dependency management.

## Problem Statement
Current issues with venv + .env approach:
1. **API keys not loading consistently** - Must call load_dotenv() in multiple files
2. **Python version inconsistencies** - Sometimes uses system Python 2.7 instead of venv Python 3.x  
3. **Manual activation required** - Must remember `source venv/bin/activate` every time
4. **Environment variables not persistent** - Lost between shell sessions
5. **Dependency management fragmented** - pip for Python, manual for system deps

## Proposed Solution
Implement Micromamba to manage:
- Python version (specify exact version)
- All Python dependencies
- Environment variables (API keys)
- System dependencies if needed
- Single activation command that handles everything

## Benefits
1. **Single source of truth** - `environment.yml` defines entire environment
2. **Consistent Python version** - No more Python 2.7 accidents
3. **Built-in env vars** - API keys set in environment, no dotenv needed
4. **Better isolation** - Complete separation from system Python
5. **Reproducible** - Anyone can recreate exact environment
6. **Cross-platform** - Works on macOS, Linux, Windows

## Implementation Approach

### Phase 1: Setup Micromamba
- Install Micromamba on system
- Create `environment.yml` with all current dependencies
- Include environment variables in the config
- Test activation and package installation

### Phase 2: Migration
- Export current pip dependencies
- Convert to conda/mamba format
- Add Python version constraint (3.11 or 3.12)
- Add API keys as environment variables
- Create activation script

### Phase 3: Code Cleanup  
- Remove all `load_dotenv()` calls
- Remove `python-dotenv` dependency
- Update README with new setup instructions
- Test all functionality

### Phase 4: Validation
- Test workflow v0.4.0 runs correctly
- Verify API keys load automatically
- Ensure all tests pass
- Document new developer setup

## Environment Configuration

### environment.yml Structure
```yaml
name: locaited
channels:
  - conda-forge
  - defaults

dependencies:
  - python=3.11
  - pip
  - pip:
    - openai
    - tavily
    - langgraph
    - langchain
    - pandas
    - pytest
    - python-dateutil

variables:
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  TAVILY_API_KEY: ${TAVILY_API_KEY}
  DATABASE_URL: sqlite:///locaited.db
  OPENAI_MODEL: gpt-5-mini
```

## Success Criteria
1. Single command environment activation: `micromamba activate locaited`
2. API keys available immediately after activation
3. Correct Python version (3.11+) always used
4. All existing functionality works without code changes
5. No more load_dotenv() calls needed
6. Clear documentation for new developer setup

## Risks & Mitigations
- **Risk**: Developer unfamiliar with Micromamba
  - **Mitigation**: Provide clear setup docs and scripts
- **Risk**: CI/CD needs updates
  - **Mitigation**: Update GitHub Actions to use Micromamba
- **Risk**: Some packages not in conda channels
  - **Mitigation**: Use pip within environment.yml for those

## Timeline
- Phase 1: 15 minutes (install and setup)
- Phase 2: 20 minutes (migration)
- Phase 3: 15 minutes (cleanup)
- Phase 4: 10 minutes (validation)
- Total: ~1 hour

## Questions for Discussion
1. Should we use Micromamba or full Mamba/Conda?
2. Python 3.11 or 3.12?
3. Should we version-lock all dependencies or just major versions?
4. Include development dependencies (pytest, black, etc.) in same environment?
5. Should API keys be in environment.yml or separate .env.secret file?