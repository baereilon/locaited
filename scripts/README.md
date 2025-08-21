# Scripts Directory

Utility scripts for development, testing, and validation of the LocAIted system.

## Structure

### benchmark/
- **benchmark_workflow.py** - Simple benchmark focusing on September events from test data

### setup/
- **setup.sh** - Environment setup automation script
- **setup_validate.py** - Validates environment configuration and dependencies

### validation/
- **test_workflow.py** - Tests the v0.4.0 workflow with ground truth events
- **validate_workflow.py** - Comprehensive workflow validation with metrics

## Usage

All Python scripts should be run from the project root with micromamba:

```bash
# Run benchmark
micromamba run -n locaited python scripts/benchmark/benchmark_workflow.py

# Validate setup
micromamba run -n locaited python scripts/setup/setup_validate.py

# Test workflow
micromamba run -n locaited python scripts/validation/test_workflow.py
```

## Note
The main benchmarking system is in `benchmarks/benchmark_system.py` which provides version-agnostic testing using the actual complete workflow.