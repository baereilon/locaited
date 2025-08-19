#!/usr/bin/env python
"""Quick script to run benchmarks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from benchmarks.benchmark_system import VersionManager, BenchmarkRunner, BenchmarkComparator


def run_baseline():
    """Create and benchmark version 0.1.0 (current state)."""
    print("\n" + "="*60)
    print("ESTABLISHING BASELINE - Version 0.1.0")
    print("="*60)
    
    # Create version 0.1.0
    vm = VersionManager()
    vm.create_version(
        "0.1.0",
        "Baseline version - current implementation",
        [
            "Basic Tavily search",
            "No domain filtering",
            "No Facebook exclusion",
            "Simple query construction"
        ]
    )
    
    # Run benchmark
    print("\nRunning baseline benchmark...")
    print("This will use ~0.05 Tavily credits (5 searches)")
    print("Auto-proceeding with benchmark...")
    
    runner = BenchmarkRunner("0.1.0")
    results = runner.run_benchmark_suite()
    
    return results


def run_improved():
    """Run benchmark for version 0.2.0 (after improvements)."""
    print("\n" + "="*60)
    print("BENCHMARKING IMPROVED VERSION - Version 0.2.0")
    print("="*60)
    
    # Create version 0.2.0
    vm = VersionManager()
    vm.create_version(
        "0.2.0",
        "Improved search with domain filtering and query optimization",
        [
            "Exclude Facebook from results",
            "Add official sources (UN, White House, NYC gov)",
            "Improved query construction with site: operators",
            "Advanced search depth for scheduled events"
        ]
    )
    
    # Run benchmark
    print("\nRunning improved version benchmark...")
    print("This will use ~0.05 Tavily credits (5 searches)")
    print("Auto-proceeding with benchmark...")
    
    runner = BenchmarkRunner("0.2.0")
    results = runner.run_benchmark_suite()
    
    return results


def compare_versions():
    """Compare v0.1.0 to v0.2.0."""
    print("\n" + "="*60)
    print("COMPARING VERSIONS")
    print("="*60)
    
    comparator = BenchmarkComparator()
    comparison = comparator.compare_versions("0.1.0", "0.2.0")
    
    return comparison


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LocAIted benchmarks")
    parser.add_argument("--baseline", action="store_true", help="Run baseline v0.1.0")
    parser.add_argument("--improved", action="store_true", help="Run improved v0.2.0")
    parser.add_argument("--compare", action="store_true", help="Compare v0.1.0 to v0.2.0")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks and compare")
    
    args = parser.parse_args()
    
    if args.all:
        # Run everything
        run_baseline()
        print("\n" + "="*60 + "\n")
        print("Baseline complete. Running improved version...")
        run_improved()
        print("\n" + "="*60 + "\n")
        compare_versions()
    elif args.baseline:
        run_baseline()
    elif args.improved:
        run_improved()
    elif args.compare:
        compare_versions()
    else:
        print("Please specify --baseline, --improved, --compare, or --all")
        parser.print_help()