# Local Files Documentation

This document explains which files/directories are kept locally but not committed to Git.

## Files/Directories in .gitignore

### Essential for Local Development (KEEP)
- `CLAUDE.md` - AI assistant context and development notes
- `cache/` - Agent caching system (speeds up development, regenerated automatically)
- `*.db` - SQLite databases (generated locally)
- `.env*` - Environment variables and API keys
- `venv/` - Python virtual environment
- `node_modules/` - Node.js dependencies for UI

### Generated During Testing (AUTO-CREATED)
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Pytest cache
- `*.pyc` - Python compiled files
- `htmlcov/` - Coverage reports
- `*.log` - Log files

### Historical Data (OPTIONAL TO KEEP LOCALLY)
These directories contain historical test results. They're gitignored but you may want to keep them locally for analysis:
- `extraction_results/` - Historical extraction test outputs
- `recommendation_results/` - Historical scoring results
- `benchmark_results_*.csv` - Benchmark outputs
- `events_for_validation_*.csv` - Validation data

## Important Notes

1. **Cache Directory**: The `cache/` directory is actively used by agents to avoid redundant API calls. It will be automatically recreated when you run the system, but keeping it saves API costs.

2. **Database Files**: `locaited.db` is referenced in the configuration. It will be created automatically when needed.

3. **Environment Files**: Never commit `.env` files. Use `.env.example` as a template.

## Directories That Should Exist (even if empty)
- `data/` - For future data files
- `logs/` - For application logs
- `reports/` - For generated reports