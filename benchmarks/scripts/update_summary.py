#!/usr/bin/env python3
"""
Update benchmark summary after running benchmarks.

This script:
1. Reads the latest benchmark results
2. Updates BENCHMARK_HISTORY.json
3. Calculates deltas from previous version
4. Optionally updates README.md
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(filepath: Path, data: Dict[str, Any]):
    """Save JSON file with pretty formatting."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def extract_metrics_from_v4(result_file: Path) -> Dict[str, Any]:
    """Extract metrics from v0.4.0 format results."""
    data = load_json(result_file)
    
    return {
        "total_events": data.get("total_events", 0),
        "avg_cost": data.get("total_cost", 0),
        "duration_seconds": data.get("duration_seconds", 0),
        "gate_decision": data.get("gate_decision", ""),
        "workflow_iterations": data.get("workflow_iterations", 1),
        "events_with_complete_info": data.get("events_with_complete_info", 0)
    }


def extract_metrics_from_v3(result_file: Path) -> Dict[str, Any]:
    """Extract metrics from v0.3.0 format results."""
    data = load_json(result_file)
    
    total_cost = 0
    total_events = 0
    total_candidates = 0
    queries_tested = 0
    
    for query_data in data.get("test_results", {}).values():
        if "metrics" in query_data:
            total_cost += query_data["metrics"].get("total_cost", 0)
            total_events += query_data["metrics"].get("total_extracted", 0)
            total_candidates += query_data["metrics"].get("total_candidates", 0)
            queries_tested += 1
    
    avg_cost = total_cost / queries_tested if queries_tested > 0 else 0
    avg_events = total_events / queries_tested if queries_tested > 0 else 0
    avg_candidates = total_candidates / queries_tested if queries_tested > 0 else 0
    
    return {
        "avg_events_found": avg_events,
        "avg_candidates": avg_candidates,
        "avg_cost": avg_cost,
        "queries_tested": queries_tested
    }


def extract_metrics_from_legacy(result_file: Path) -> Dict[str, Any]:
    """Extract metrics from v0.1.0/v0.2.0 format results."""
    data = load_json(result_file)
    
    metrics = data.get("overall_metrics", {})
    return {
        "avg_events_found": metrics.get("avg_unique_events_per_query", 0),
        "avg_results_per_query": metrics.get("avg_results_per_query", 0),
        "info_completeness": metrics.get("pct_with_basic_info", 0),
        "avg_cost": metrics.get("total_api_cost", 0),
        "total_unique_events": metrics.get("total_unique_events", 0)
    }


def update_benchmark_history(
    version: str,
    result_file: Path,
    git_commit: Optional[str] = None,
    improvements: Optional[list] = None
):
    """Update the benchmark history with new results."""
    
    # Load existing history
    history_file = Path("benchmarks/summary/BENCHMARK_HISTORY.json")
    if history_file.exists():
        history = load_json(history_file)
    else:
        history = {
            "versions": [],
            "current_version": version,
            "last_updated": datetime.now().isoformat()
        }
    
    # Extract metrics based on version format
    if version.startswith("0.4"):
        metrics = extract_metrics_from_v4(result_file)
    elif version.startswith("0.3"):
        metrics = extract_metrics_from_v3(result_file)
    else:
        metrics = extract_metrics_from_legacy(result_file)
    
    # Create new version entry
    new_entry = {
        "version": version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "git_commit": git_commit or "unknown",
        "metrics": metrics,
        "improvements": improvements or [],
        "benchmark_file": str(result_file.relative_to(Path.cwd()))
    }
    
    # Check if version already exists
    existing_idx = None
    for i, v in enumerate(history["versions"]):
        if v["version"] == version:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # Update existing entry
        history["versions"][existing_idx] = new_entry
        print(f"Updated existing entry for version {version}")
    else:
        # Add new entry
        history["versions"].append(new_entry)
        print(f"Added new entry for version {version}")
    
    # Update metadata
    history["current_version"] = version
    history["last_updated"] = datetime.now().isoformat()
    
    # Save updated history
    save_json(history_file, history)
    print(f"Updated {history_file}")
    
    return history


def calculate_deltas(history: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Calculate changes from previous version."""
    
    versions = history["versions"]
    current_idx = None
    
    for i, v in enumerate(versions):
        if v["version"] == version:
            current_idx = i
            break
    
    if current_idx is None or current_idx == 0:
        return {}
    
    current = versions[current_idx]["metrics"]
    previous = versions[current_idx - 1]["metrics"]
    prev_version = versions[current_idx - 1]["version"]
    
    deltas = {
        "compared_to": prev_version,
        "changes": {}
    }
    
    # Calculate percentage changes for common metrics
    for key in current:
        if key in previous and isinstance(current[key], (int, float)):
            old_val = previous[key]
            new_val = current[key]
            if old_val != 0:
                pct_change = ((new_val - old_val) / old_val) * 100
                deltas["changes"][key] = {
                    "old": old_val,
                    "new": new_val,
                    "change_pct": round(pct_change, 1)
                }
    
    return deltas


def main():
    parser = argparse.ArgumentParser(description="Update benchmark summary")
    parser.add_argument("version", help="Version number (e.g., 0.4.1)")
    parser.add_argument("result_file", help="Path to benchmark result file")
    parser.add_argument("--git-commit", help="Git commit hash")
    parser.add_argument("--improvements", nargs="+", help="List of improvements")
    parser.add_argument("--update-readme", action="store_true", help="Update README.md")
    
    args = parser.parse_args()
    
    result_file = Path(args.result_file)
    if not result_file.exists():
        print(f"Error: Result file {result_file} not found")
        return 1
    
    # Update history
    history = update_benchmark_history(
        args.version,
        result_file,
        args.git_commit,
        args.improvements
    )
    
    # Calculate deltas
    deltas = calculate_deltas(history, args.version)
    if deltas:
        print(f"\nChanges from {deltas['compared_to']}:")
        for metric, change in deltas["changes"].items():
            symbol = "📈" if change["change_pct"] > 0 else "📉"
            print(f"  {symbol} {metric}: {change['old']} → {change['new']} ({change['change_pct']:+.1f}%)")
    
    if args.update_readme:
        print("\nTODO: README update not yet implemented")
    
    return 0


if __name__ == "__main__":
    exit(main())