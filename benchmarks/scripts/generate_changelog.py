#!/usr/bin/env python3
"""
Generate changelog for a version based on benchmark improvements.

This script creates markdown-formatted release notes from benchmark data.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List


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


def get_previous_version(history: Dict[str, Any], version: str) -> str:
    """Get the previous version number."""
    versions = history["versions"]
    for i, v in enumerate(versions):
        if v["version"] == version and i > 0:
            return versions[i-1]["version"]
    return None


def format_metric_improvement(key: str, old_val: Any, new_val: Any) -> str:
    """Format a metric improvement for the changelog."""
    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
        if old_val == 0:
            return f"**{key}**: {new_val} (new metric)"
        else:
            pct_change = ((new_val - old_val) / abs(old_val)) * 100
            if abs(pct_change) > 1:
                return f"**{key}**: {old_val} → {new_val} ({pct_change:+.1f}%)"
            else:
                return f"**{key}**: {new_val}"
    return f"**{key}**: {new_val}"


def categorize_improvements(improvements: List[str]) -> Dict[str, List[str]]:
    """Categorize improvements by type."""
    categories = {
        "Architecture": [],
        "Performance": [],
        "Quality": [],
        "Cost": [],
        "Features": [],
        "Other": []
    }
    
    for improvement in improvements:
        lower = improvement.lower()
        if any(word in lower for word in ["architecture", "pipeline", "langraph", "agent"]):
            categories["Architecture"].append(improvement)
        elif any(word in lower for word in ["cost", "price", "budget", "cheaper"]):
            categories["Cost"].append(improvement)
        elif any(word in lower for word in ["quality", "validation", "verification", "accuracy"]):
            categories["Quality"].append(improvement)
        elif any(word in lower for word in ["performance", "speed", "fast", "optimization"]):
            categories["Performance"].append(improvement)
        elif any(word in lower for word in ["feature", "added", "new", "implement"]):
            categories["Features"].append(improvement)
        else:
            categories["Other"].append(improvement)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def generate_changelog(version_data: Dict[str, Any], prev_data: Dict[str, Any] = None) -> str:
    """Generate markdown changelog for a version."""
    version = version_data["version"]
    date = version_data["date"]
    commit = version_data.get("git_commit", "unknown")
    
    changelog = f"# Release Notes - v{version}\n\n"
    changelog += f"**Release Date:** {date}  \n"
    changelog += f"**Git Commit:** {commit}  \n\n"
    
    # Executive Summary
    if prev_data:
        prev_version = prev_data["version"]
        changelog += f"## 📊 Executive Summary\n\n"
        changelog += f"Version {version} represents a significant evolution from v{prev_version}, "
        
        # Calculate key improvements
        curr_metrics = version_data["metrics"]
        prev_metrics = prev_data["metrics"]
        
        improvements_summary = []
        
        # Cost comparison
        if "avg_cost" in curr_metrics and "avg_cost" in prev_metrics:
            curr_cost = curr_metrics["avg_cost"]
            prev_cost = prev_metrics["avg_cost"]
            if prev_cost > 0:
                cost_change = ((curr_cost - prev_cost) / prev_cost) * 100
                if cost_change < -10:
                    improvements_summary.append(f"{abs(cost_change):.0f}% cost reduction")
                elif cost_change > 10:
                    improvements_summary.append(f"{cost_change:.0f}% cost increase")
        
        # Quality comparison
        if "info_completeness" in curr_metrics and "info_completeness" in prev_metrics:
            curr_qual = curr_metrics["info_completeness"]
            prev_qual = prev_metrics["info_completeness"]
            if prev_qual > 0:
                qual_change = ((curr_qual - prev_qual) / prev_qual) * 100
                if qual_change > 10:
                    improvements_summary.append(f"{qual_change:.0f}% quality improvement")
        
        if improvements_summary:
            changelog += f"featuring {', '.join(improvements_summary)}.\n\n"
        else:
            changelog += "with architectural improvements and optimizations.\n\n"
    
    # Key Improvements
    if version_data.get("improvements"):
        changelog += "## 🚀 Key Improvements\n\n"
        
        categorized = categorize_improvements(version_data["improvements"])
        
        for category, items in categorized.items():
            changelog += f"### {category}\n"
            for item in items:
                changelog += f"- {item}\n"
            changelog += "\n"
    
    # Performance Metrics
    changelog += "## 📈 Performance Metrics\n\n"
    
    if prev_data:
        changelog += "### Compared to Previous Version\n\n"
        changelog += "| Metric | Previous | Current | Change |\n"
        changelog += "|--------|----------|---------|--------|\n"
        
        curr_metrics = version_data["metrics"]
        prev_metrics = prev_data["metrics"]
        
        # Find common metrics
        common_metrics = set(curr_metrics.keys()) & set(prev_metrics.keys())
        
        for key in sorted(common_metrics):
            curr_val = curr_metrics[key]
            prev_val = prev_metrics[key]
            
            if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
                if prev_val == 0:
                    change = "New"
                else:
                    pct = ((curr_val - prev_val) / abs(prev_val)) * 100
                    if abs(pct) < 0.1:
                        change = "→"
                    elif pct > 0:
                        change = f"↑ {pct:+.1f}%"
                    else:
                        change = f"↓ {pct:+.1f}%"
                
                # Format numbers
                if isinstance(curr_val, float):
                    curr_str = f"{curr_val:.3f}" if curr_val < 1 else f"{curr_val:.1f}"
                    prev_str = f"{prev_val:.3f}" if prev_val < 1 else f"{prev_val:.1f}"
                else:
                    curr_str = str(curr_val)
                    prev_str = str(prev_val)
                
                # Clean up metric name
                display_name = key.replace("_", " ").title()
                changelog += f"| {display_name} | {prev_str} | {curr_str} | {change} |\n"
    else:
        changelog += "### Current Version Metrics\n\n"
        for key, value in version_data["metrics"].items():
            display_name = key.replace("_", " ").title()
            if isinstance(value, float):
                value_str = f"{value:.3f}" if value < 1 else f"{value:.1f}"
            else:
                value_str = str(value)
            changelog += f"- **{display_name}**: {value_str}\n"
    
    changelog += "\n"
    
    # Known Issues
    if version_data.get("regressions"):
        changelog += "## ⚠️ Known Issues\n\n"
        for regression in version_data["regressions"]:
            changelog += f"- {regression}\n"
        changelog += "\n"
    
    # Technical Details
    changelog += "## 🔧 Technical Details\n\n"
    changelog += f"- **Test Queries Used**: {', '.join(version_data.get('test_queries_used', ['Unknown']))}\n"
    changelog += f"- **Benchmark File**: `{version_data.get('benchmark_file', 'Unknown')}`\n"
    
    # Testing
    changelog += "\n## 🧪 Testing\n\n"
    changelog += "To reproduce these benchmark results:\n\n"
    changelog += "```bash\n"
    changelog += "# Run the benchmark suite\n"
    changelog += "micromamba run -n locaited python benchmarks/benchmark_system.py\n"
    changelog += "\n"
    changelog += "# Compare with previous version\n"
    if prev_data:
        changelog += f"python benchmarks/scripts/compare_versions.py {prev_data['version']} {version}\n"
    else:
        changelog += f"python benchmarks/scripts/compare_versions.py 0.1.0 {version}\n"
    changelog += "```\n"
    
    return changelog


def main():
    parser = argparse.ArgumentParser(description="Generate changelog for a version")
    parser.add_argument("version", help="Version number (e.g., 0.4.0)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "text"], default="markdown",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Load history
    history_file = Path("benchmarks/summary/BENCHMARK_HISTORY.json")
    if not history_file.exists():
        print(f"Error: {history_file} not found")
        return 1
    
    history = load_json(history_file)
    
    # Get version data
    try:
        version_data = get_version_data(history, args.version)
    except ValueError as e:
        print(f"Error: {e}")
        print(f"Available versions: {', '.join(v['version'] for v in history['versions'])}")
        return 1
    
    # Get previous version data if available
    prev_version = get_previous_version(history, args.version)
    prev_data = None
    if prev_version:
        prev_data = get_version_data(history, prev_version)
    
    # Generate changelog
    changelog = generate_changelog(version_data, prev_data)
    
    # Output
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w') as f:
            f.write(changelog)
        print(f"Changelog written to {output_file}")
    else:
        print(changelog)
    
    return 0


if __name__ == "__main__":
    exit(main())