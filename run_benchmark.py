#!/usr/bin/env python
"""Run benchmark system with git-based version management."""

import argparse
import sys
from pathlib import Path
import json
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent / "benchmarks"))
from benchmark_system import BenchmarkSystem, BenchmarkComparator


def get_current_git_version():
    """Get the current git tag or commit hash."""
    try:
        # Try to get the current tag
        tag = subprocess.check_output(
            ["git", "describe", "--exact-match", "--tags"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except subprocess.CalledProcessError:
        # No exact tag, get commit hash
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                text=True
            ).strip()
            # Check if there are uncommitted changes
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True
            ).strip()
            if status:
                return "{}-dirty".format(commit)
            return commit
        except subprocess.CalledProcessError:
            return datetime.now().strftime("%Y%m%d_%H%M%S")


def list_git_tags():
    """List all available git tags."""
    try:
        tags = subprocess.check_output(
            ["git", "tag", "-l"],
            text=True
        ).strip().split('\n')
        return [t for t in tags if t]  # Filter empty strings
    except subprocess.CalledProcessError:
        return []


def checkout_version(version):
    """Checkout a specific git version (tag or commit)."""
    try:
        # Stash any uncommitted changes
        subprocess.run(["git", "stash"], capture_output=True)
        # Checkout the version
        subprocess.run(["git", "checkout", version], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("Error checking out {}: {}".format(version, e))
        return False


def main():
    parser = argparse.ArgumentParser(description="Run LocAIted benchmark")
    parser.add_argument("--version", type=str,
                       help="Version label for this benchmark run (default: current git tag/commit)")
    parser.add_argument("--compare", nargs=2, metavar=('VERSION1', 'VERSION2'),
                       help="Compare two versions (e.g., --compare v0.2.0 v0.3.0)")
    parser.add_argument("--list", action="store_true",
                       help="List available benchmark results")
    parser.add_argument("--list-tags", action="store_true",
                       help="List available git tags")
    parser.add_argument("--checkout-and-run", type=str,
                       help="Checkout a git tag/commit and run benchmark (WARNING: will stash current changes)")
    
    args = parser.parse_args()
    
    if args.list_tags:
        # List git tags
        tags = list_git_tags()
        if tags:
            print("\nAvailable git tags:")
            for tag in tags:
                print("  {}".format(tag))
        else:
            print("No git tags found")
        
        # Also show current version
        current = get_current_git_version()
        print("\nCurrent version: {}".format(current))
        return
    
    if args.list:
        # List available benchmark results
        results_dir = Path("benchmarks/results")
        if results_dir.exists():
            versions = [d.name for d in results_dir.iterdir() if d.is_dir()]
            if versions:
                print("\nAvailable benchmark results:")
                for v in sorted(versions):
                    result_file = results_dir / v / "benchmark_results.json"
                    if result_file.exists():
                        with open(result_file) as f:
                            data = json.load(f)
                        timestamp = data.get("version_info", {}).get("timestamp", "Unknown")
                        events = len(data.get("events_for_validation", []))
                        git_commit = data.get("version_info", {}).get("git_commit", "Unknown")
                        print("  {}: {} events, commit={}, run at {}".format(v, events, git_commit, timestamp))
            else:
                print("No benchmark results found")
        return
    
    if args.compare:
        # Compare two versions
        v1, v2 = args.compare
        # Remove 'v' prefix if present for consistency
        v1 = v1.lstrip('v')
        v2 = v2.lstrip('v')
        print("\nComparing {} vs {}...".format(v1, v2))
        comparator = BenchmarkComparator()
        comparator.compare_versions(v1, v2)
    
    elif args.checkout_and_run:
        # Checkout a specific version and run benchmark
        version = args.checkout_and_run
        print("\nWARNING: This will stash any uncommitted changes and checkout {}".format(version))
        print("Continue? (y/n): ", end="")
        if input().lower() != 'y':
            print("Aborted")
            return
        
        # Save current branch/commit
        current = get_current_git_version()
        
        # Checkout the requested version
        if checkout_version(version):
            # Run benchmark
            clean_version = version.lstrip('v') if version.startswith('v') else version
            print("\nRunning benchmark for {}...".format(version))
            benchmark = BenchmarkSystem(clean_version)
            results = benchmark.run_benchmark_suite()
            print("\nResults for {} saved".format(clean_version))
            
            # Return to original version
            print("\nReturning to {}...".format(current))
            subprocess.run(["git", "checkout", current], capture_output=True)
            subprocess.run(["git", "stash", "pop"], capture_output=True)
        else:
            print("Failed to checkout {}".format(version))
    
    else:
        # Run benchmark with version
        if args.version:
            version = args.version.lstrip('v')  # Remove 'v' prefix for consistency
            print("\nRunning benchmark for version {}...".format(version))
        else:
            # Use current git version
            git_version = get_current_git_version()
            version = git_version.lstrip('v') if git_version.startswith('v') else git_version
            print("\nRunning benchmark for current code (version: {})...".format(version))
        
        benchmark = BenchmarkSystem(version)
        results = benchmark.run_benchmark_suite()
        print("\nResults for v{} saved".format(version))
        print("Total events generated: {}".format(len(results['events_for_validation'])))
        
        # Offer to compare with another version if others exist
        results_dir = Path("benchmarks/results")
        other_versions = [d.name.replace('v', '') for d in results_dir.iterdir() 
                         if d.is_dir() and d.name != "v{}".format(version)]
        
        if other_versions:
            print("\nOther versions available for comparison: {}".format(', '.join(other_versions)))
            print("Enter a version to compare with (or press Enter to skip): ", end="")
            compare_with = input().strip().lstrip('v')
            if compare_with and compare_with in other_versions:
                comparator = BenchmarkComparator()
                comparator.compare_versions(compare_with, version)


if __name__ == "__main__":
    main()