# Benchmark Summary System

This directory contains the centralized benchmark tracking system for LocAIted, providing historical performance data and tools for analysis.

## 📊 Quick Overview

The benchmark system tracks key performance metrics across versions:
- **Event Discovery Rate**: How many relevant events are found
- **Information Completeness**: Percentage of events with date, time, and location
- **API Cost**: Average cost per query
- **Deduplication Rate**: Effectiveness at removing duplicate events
- **Pipeline Efficiency**: Event retention through each processing stage

## 📁 Directory Structure

```
summary/
├── BENCHMARK_HISTORY.json    # Master tracking file (single source of truth)
├── version_comparisons.json  # Pre-computed version-to-version comparisons
└── README.md                  # This file
```

## 🔧 Available Scripts

### 1. Update Summary After Benchmark
```bash
python benchmarks/scripts/update_summary.py <version> <result_file> [options]

# Example:
python benchmarks/scripts/update_summary.py 0.5.0 \
    benchmarks/results/v0.5.0/benchmark_results.json \
    --git-commit abc123 \
    --improvements "Added caching" "Optimized prompts"
```

### 2. Compare Two Versions
```bash
python benchmarks/scripts/compare_versions.py <version1> <version2> [options]

# Examples:
python benchmarks/scripts/compare_versions.py 0.3.0 0.4.0          # Detailed comparison
python benchmarks/scripts/compare_versions.py 0.3.0 0.4.0 --brief  # Summary only
python benchmarks/scripts/compare_versions.py 0.3.0 0.4.0 --save   # Save to file
```

### 3. Generate Release Changelog
```bash
python benchmarks/scripts/generate_changelog.py <version> [options]

# Examples:
python benchmarks/scripts/generate_changelog.py 0.4.0                    # Print to stdout
python benchmarks/scripts/generate_changelog.py 0.4.0 --output CHANGELOG.md  # Save to file
```

## 📈 Performance Evolution

| Version | Date | Cost | Quality | Key Achievement |
|---------|------|------|---------|-----------------|
| v0.1.0 | 2025-08-18 | $0.05 | 14% | Initial Tavily integration |
| v0.2.0 | 2025-08-18 | $0.05 | 8% | 53% more search coverage |
| v0.3.0 | 2025-08-19 | $0.38 | 11% | LLM orchestration added |
| v0.4.0 | 2025-08-20 | $0.03 | 100%* | Multi-agent LangGraph pipeline |

*Quality metric redefined in v0.4.0 to focus on fewer, higher-quality events

## 🎯 Metrics Definitions

### Core Metrics
- **avg_events_found**: Average number of unique events discovered per query
- **info_completeness**: Percentage of events with complete information (date, time, location)
- **avg_cost**: Average API cost per query in USD
- **dedup_rate**: Percentage of duplicate events successfully removed
- **pipeline_efficiency**: Ratio of final curated events to initial candidates

### Version-Specific Metrics
- **v0.3.0+**: Added pipeline flow tracking (researcher → fact_checker → publisher)
- **v0.4.0+**: Added gate decision tracking and workflow iterations

## 🚀 Workflow for New Versions

### 1. Run Benchmark
```bash
# Run the standard benchmark suite
micromamba run -n locaited python benchmarks/benchmark_system.py
```

### 2. Update Summary
```bash
# Update the tracking system with results
python benchmarks/scripts/update_summary.py 0.5.0 \
    benchmarks/results/v0.5.0/benchmark_results.json \
    --git-commit $(git rev-parse HEAD) \
    --improvements "Your improvements here"
```

### 3. Compare with Previous
```bash
# Generate comparison report
python benchmarks/scripts/compare_versions.py 0.4.0 0.5.0
```

### 4. Generate Changelog
```bash
# Create release notes
python benchmarks/scripts/generate_changelog.py 0.5.0 \
    --output RELEASE_NOTES_v0.5.0.md
```

## 📝 Data Format

### BENCHMARK_HISTORY.json Structure
```json
{
  "versions": [
    {
      "version": "0.4.0",
      "date": "2025-08-20",
      "git_commit": "abc123",
      "metrics": {
        "avg_events_found": 10,
        "info_completeness": 100,
        "avg_cost": 0.03
      },
      "improvements": ["List of improvements"],
      "regressions": ["List of regressions if any"],
      "test_queries_used": ["query1", "query2"],
      "benchmark_file": "path/to/raw/results.json"
    }
  ],
  "current_version": "0.4.0",
  "last_updated": "2025-08-20T14:00:00"
}
```

## 🔄 Updating the Main README

After running benchmarks and updating the summary:

```bash
# The benchmark table in the main README can be updated manually
# Future: add --update-readme flag to update_summary.py
```

## 📊 Analyzing Trends

To analyze performance trends across all versions:

```python
import json
import matplotlib.pyplot as plt

with open('benchmarks/summary/BENCHMARK_HISTORY.json') as f:
    history = json.load(f)

versions = [v['version'] for v in history['versions']]
costs = [v['metrics']['avg_cost'] for v in history['versions']]

plt.plot(versions, costs)
plt.title('API Cost Evolution')
plt.xlabel('Version')
plt.ylabel('Cost ($)')
plt.show()
```

## 🐛 Troubleshooting

### Missing Metrics
Some metrics may not be available in older versions. The scripts handle this gracefully by:
- Showing "N/A" for missing metrics in comparisons
- Skipping percentage calculations when baseline is missing
- Noting new metrics as "added" in comparison reports

### File Not Found
Ensure you're running scripts from the project root:
```bash
cd /path/to/locaited
python benchmarks/scripts/compare_versions.py 0.3.0 0.4.0
```

## 🔗 Related Documentation

- [Main README](../../README.md) - Project overview and setup
- [Benchmark System](../benchmark_system.py) - Main benchmark runner
- [Test Queries](../test_queries.json) - Standard test suite
- [Raw Results](../results/) - Version-specific raw benchmark data