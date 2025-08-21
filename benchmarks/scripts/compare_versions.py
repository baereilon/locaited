#!/usr/bin/env python3
"""
Compare benchmark results between versions.

This script generates detailed comparison reports between any two versions.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_version_data(history: Dict[str, Any], version: str) -> Dict[str, Any]:
    """Get data for a specific version."""
    for v in history["versions"]:
        if v["version"] == version:
            return v
    raise ValueError(f"Version {version} not found in history")


def compare_metrics(v1_data: Dict[str, Any], v2_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compare metrics between two versions."""
    v1_metrics = v1_data["metrics"]
    v2_metrics = v2_data["metrics"]
    
    comparison = {
        "improved": {},
        "regressed": {},
        "unchanged": {},
        "added": {},
        "removed": {}
    }
    
    # Find common metrics
    v1_keys = set(v1_metrics.keys())
    v2_keys = set(v2_metrics.keys())
    
    common_keys = v1_keys & v2_keys
    added_keys = v2_keys - v1_keys
    removed_keys = v1_keys - v2_keys
    
    # Compare common metrics
    for key in common_keys:
        v1_val = v1_metrics[key]
        v2_val = v2_metrics[key]
        
        if isinstance(v1_val, (int, float)) and isinstance(v2_val, (int, float)):
            if v1_val == 0:
                if v2_val != 0:
                    pct_change = float('inf')
                else:
                    pct_change = 0
            else:
                pct_change = ((v2_val - v1_val) / abs(v1_val)) * 100
            
            metric_data = {
                "old": v1_val,
                "new": v2_val,
                "change": v2_val - v1_val,
                "change_pct": pct_change
            }
            
            # Determine if improvement or regression based on metric name
            if abs(pct_change) < 0.1:
                comparison["unchanged"][key] = metric_data
            elif key in ["avg_cost", "duration_seconds", "workflow_iterations"]:
                # Lower is better
                if v2_val < v1_val:
                    comparison["improved"][key] = metric_data
                else:
                    comparison["regressed"][key] = metric_data
            else:
                # Higher is better
                if v2_val > v1_val:
                    comparison["improved"][key] = metric_data
                else:
                    comparison["regressed"][key] = metric_data
    
    # Added metrics
    for key in added_keys:
        comparison["added"][key] = v2_metrics[key]
    
    # Removed metrics
    for key in removed_keys:
        comparison["removed"][key] = v1_metrics[key]
    
    return comparison


def format_metric_change(key: str, data: Dict[str, Any]) -> str:
    """Format a metric change for display."""
    if isinstance(data, dict) and "old" in data:
        old = data["old"]
        new = data["new"]
        pct = data["change_pct"]
        
        if isinstance(old, float) or isinstance(new, float):
            if pct == float('inf'):
                return f"{key}: {old:.2f} → {new:.2f} (new)"
            else:
                return f"{key}: {old:.2f} → {new:.2f} ({pct:+.1f}%)"
        else:
            if pct == float('inf'):
                return f"{key}: {old} → {new} (new)"
            else:
                return f"{key}: {old} → {new} ({pct:+.1f}%)"
    else:
        return f"{key}: {data}"


def print_comparison_report(v1: str, v2: str, v1_data: Dict, v2_data: Dict, comparison: Dict):
    """Print a formatted comparison report."""
    print(f"\n{'='*60}")
    print(f"BENCHMARK COMPARISON: v{v1} → v{v2}")
    print(f"{'='*60}")
    
    print(f"\n📊 VERSION DETAILS")
    print(f"  v{v1}: {v1_data['date']} (commit: {v1_data.get('git_commit', 'unknown')[:7]})")
    print(f"  v{v2}: {v2_data['date']} (commit: {v2_data.get('git_commit', 'unknown')[:7]})")
    
    if comparison["improved"]:
        print(f"\n✅ IMPROVEMENTS ({len(comparison['improved'])})")
        for key, data in comparison["improved"].items():
            print(f"  • {format_metric_change(key, data)}")
    
    if comparison["regressed"]:
        print(f"\n⚠️  REGRESSIONS ({len(comparison['regressed'])})")
        for key, data in comparison["regressed"].items():
            print(f"  • {format_metric_change(key, data)}")
    
    if comparison["added"]:
        print(f"\n➕ NEW METRICS ({len(comparison['added'])})")
        for key, value in comparison["added"].items():
            print(f"  • {key}: {value}")
    
    if comparison["removed"]:
        print(f"\n➖ REMOVED METRICS ({len(comparison['removed'])})")
        for key, value in comparison["removed"].items():
            print(f"  • {key}: {value}")
    
    # Key improvements and regressions from metadata
    if v2_data.get("improvements"):
        print(f"\n🚀 KEY IMPROVEMENTS")
        for improvement in v2_data["improvements"]:
            print(f"  • {improvement}")
    
    if v2_data.get("regressions"):
        print(f"\n⚠️  KNOWN ISSUES")
        for regression in v2_data["regressions"]:
            print(f"  • {regression}")
    
    # Summary
    print(f"\n📈 SUMMARY")
    total_metrics = len(comparison["improved"]) + len(comparison["regressed"]) + len(comparison["unchanged"])
    if total_metrics > 0:
        improvement_rate = (len(comparison["improved"]) / total_metrics) * 100
        print(f"  • Improvement rate: {improvement_rate:.1f}%")
        print(f"  • {len(comparison['improved'])} improvements, {len(comparison['regressed'])} regressions")
    
    # Highlight major changes
    major_changes = []
    for key, data in {**comparison["improved"], **comparison["regressed"]}.items():
        if abs(data["change_pct"]) > 50:
            major_changes.append((key, data["change_pct"]))
    
    if major_changes:
        print(f"\n💡 MAJOR CHANGES (>50%)")
        for key, pct in sorted(major_changes, key=lambda x: abs(x[1]), reverse=True):
            symbol = "📈" if pct > 0 else "📉"
            print(f"  {symbol} {key}: {pct:+.1f}%")
    
    print(f"\n{'='*60}\n")


def save_comparison(v1: str, v2: str, comparison: Dict[str, Any]):
    """Save comparison to version_comparisons.json."""
    comp_file = Path("benchmarks/summary/version_comparisons.json")
    
    if comp_file.exists():
        comparisons = load_json(comp_file)
    else:
        comparisons = {}
    
    key = f"v{v1}_to_v{v2}"
    
    # Calculate summary statistics
    total_improved = len(comparison["improved"])
    total_regressed = len(comparison["regressed"])
    
    # Find most significant changes
    cost_change = None
    quality_change = None
    
    for metric_key, data in comparison["improved"].items():
        if "cost" in metric_key:
            cost_change = data["change_pct"]
        if "completeness" in metric_key or "quality" in metric_key:
            quality_change = data["change_pct"]
    
    for metric_key, data in comparison["regressed"].items():
        if "cost" in metric_key:
            cost_change = data["change_pct"]
        if "completeness" in metric_key or "quality" in metric_key:
            quality_change = data["change_pct"]
    
    comparisons[key] = {
        "cost_change": cost_change,
        "quality_change": quality_change,
        "total_improvements": total_improved,
        "total_regressions": total_regressed,
        "details": comparison
    }
    
    with open(comp_file, 'w') as f:
        json.dump(comparisons, f, indent=2)
    
    print(f"Comparison saved to {comp_file}")


def main():
    parser = argparse.ArgumentParser(description="Compare benchmark results between versions")
    parser.add_argument("version1", help="First version (e.g., 0.3.0)")
    parser.add_argument("version2", help="Second version (e.g., 0.4.0)")
    parser.add_argument("--save", action="store_true", help="Save comparison to file")
    parser.add_argument("--brief", action="store_true", help="Show brief summary only")
    
    args = parser.parse_args()
    
    # Load history
    history_file = Path("benchmarks/summary/BENCHMARK_HISTORY.json")
    if not history_file.exists():
        print(f"Error: {history_file} not found")
        return 1
    
    history = load_json(history_file)
    
    # Get version data
    try:
        v1_data = get_version_data(history, args.version1)
        v2_data = get_version_data(history, args.version2)
    except ValueError as e:
        print(f"Error: {e}")
        print(f"Available versions: {', '.join(v['version'] for v in history['versions'])}")
        return 1
    
    # Compare metrics
    comparison = compare_metrics(v1_data, v2_data)
    
    # Print report
    if args.brief:
        print(f"\nv{args.version1} → v{args.version2}: "
              f"{len(comparison['improved'])} improvements, "
              f"{len(comparison['regressed'])} regressions")
    else:
        print_comparison_report(args.version1, args.version2, v1_data, v2_data, comparison)
    
    # Save if requested
    if args.save:
        save_comparison(args.version1, args.version2, comparison)
    
    return 0


if __name__ == "__main__":
    exit(main())