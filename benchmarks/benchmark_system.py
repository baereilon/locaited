"""Benchmark system - Uses actual complete agent workflow and is version-agnostic."""

import json
import csv
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, TypedDict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent

# Import the actual workflow
from agents.workflow import WorkflowState, create_workflow


class BenchmarkSystem:
    """Version-agnostic benchmark system that uses the actual complete workflow."""
    
    def __init__(self, version: str = None):
        """Initialize benchmark system.
        
        Args:
            version: Version string (e.g., "0.3.0"). If None, uses current timestamp.
        """
        self.version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path(f"benchmarks/results/v{self.version}")
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        # Load test queries
        self.test_queries_file = Path("benchmarks/test_queries.json")
        with open(self.test_queries_file) as f:
            self.test_data = json.load(f)
    
    def capture_version_info(self) -> Dict:
        """Capture current version information."""
        try:
            # Get git commit hash
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                text=True
            ).strip()[:8]
        except:
            git_commit = "no-git"
        
        try:
            # Get git branch
            git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True
            ).strip()
        except:
            git_branch = "unknown"
        
        return {
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "git_commit": git_commit,
            "git_branch": git_branch
        }
    
    def run_complete_workflow(self, query: str, query_id: str = None) -> Dict:
        """
        Run the COMPLETE workflow as in test_complete_workflow.py.
        
        This uses the actual LangGraph workflow with:
        1. Editor builds profile and plans strategy
        2. Researcher searches (with multi-search and exclusions)
        3. Fact-Checker extracts and deduplicates with LLM
        4. Publisher scores and makes gate decisions
        5. Potential cycles back to Editor if needed
        
        NO ADDITIONAL DEDUPLICATION IS PERFORMED - we use exactly what the workflow returns.
        
        Args:
            query: The search query
            query_id: Optional ID for tracking
            
        Returns:
            Complete workflow results
        """
        results = {
            "query": query,
            "query_id": query_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Prepare initial state for LangGraph workflow
            initial_state = {
                "query_spec": {
                    "text": query,
                    "city": "NYC",
                    "date_from": datetime.now(),
                    "date_to": datetime.now() + timedelta(days=30),
                    "model": "gpt-3.5-turbo",
                    "version": self.version
                },
                "user_profile": {},  # Will be built by Editor
                "candidates": [],
                "extracted": [],
                "top10": [],
                "decision": {"action": "accept", "notes": ""},
                "cycle_count": 0,
                "total_cost": 0.0,
                "errors": [],
                "logs": []
            }
            
            # Create and run the actual workflow
            print(f"  Running LangGraph workflow...")
            app = create_workflow()
            
            # Set recursion limit to prevent infinite loops
            config = {"recursion_limit": 3}
            final_state = app.invoke(initial_state, config=config)
            
            # Extract results from final state
            results["workflow_state"] = {
                "cycles": final_state["cycle_count"],
                "total_cost": final_state["total_cost"],
                "candidates_found": len(final_state["candidates"]),
                "events_extracted": len(final_state["extracted"]),
                "recommendations": len(final_state["top10"]),
                "final_decision": final_state["decision"],
                "logs": final_state["logs"],
                "errors": final_state["errors"]
            }
            
            # Extract metrics for analysis (v0.3.0: Enhanced pipeline flow metrics)
            results["metrics"] = {
                "total_candidates": len(final_state["candidates"]),
                "total_extracted": len(final_state["extracted"]),
                "total_scored": len(final_state["top10"]),
                "cycles_performed": final_state["cycle_count"],
                "total_cost": final_state["total_cost"]
            }
            
            # v0.3.0: Pipeline flow metrics
            results["pipeline_flow"] = {
                "researcher_output": len(final_state["candidates"]),
                "fact_checker_input": len(final_state["candidates"]),
                "fact_checker_output": len(final_state["extracted"]),
                "publisher_input": len(final_state["extracted"]),
                "publisher_output": len(final_state["top10"]),
                "deduplication_rate": 0
            }
            
            # Calculate deduplication effectiveness
            if results["pipeline_flow"]["fact_checker_input"] > 0:
                dedupe_rate = ((results["pipeline_flow"]["fact_checker_input"] - 
                              results["pipeline_flow"]["fact_checker_output"]) / 
                              results["pipeline_flow"]["fact_checker_input"]) * 100
                results["pipeline_flow"]["deduplication_rate"] = round(dedupe_rate, 1)
            
            # Count events with basic info from extracted events
            if final_state["extracted"]:
                basic_info_count = sum(1 for e in final_state["extracted"] 
                                     if e.get("has_basic_info", False))
                results["metrics"]["events_with_basic_info"] = basic_info_count
                results["metrics"]["basic_info_percentage"] = (basic_info_count / len(final_state["extracted"])) * 100
            else:
                results["metrics"]["events_with_basic_info"] = 0
                results["metrics"]["basic_info_percentage"] = 0
            
            # Store final events for validation
            results["final_events"] = final_state["top10"]
            
            print(f"     Cycles: {final_state['cycle_count']}, Cost: ${final_state['total_cost']:.4f}")
            print(f"     Pipeline: {len(final_state['candidates'])} candidates → {len(final_state['extracted'])} unique events → {len(final_state['top10'])} scored")
            if results["pipeline_flow"]["deduplication_rate"] > 0:
                print(f"     Deduplication: {results['pipeline_flow']['deduplication_rate']:.1f}% removed")
            
        except Exception as e:
            print(f"     ERROR: {str(e)}")
            results["error"] = str(e)
            results["metrics"] = {
                "total_candidates": 0,
                "total_extracted": 0,
                "total_scored": 0,
                "cycles_performed": 0,
                "total_cost": 0
            }
        
        return results
    
    def run_benchmark_suite(self) -> Dict:
        """Run complete benchmark suite using actual complete workflow."""
        
        print(f"\n{'='*60}")
        print(f"BENCHMARK v{self.version} - Complete LangGraph Workflow")
        print(f"{'='*60}\n")
        
        # Capture version info
        version_info = self.capture_version_info()
        
        # Results storage
        all_results = {
            "version_info": version_info,
            "test_results": {},
            "summary": {},
            "events_for_validation": []
        }
        
        # Run each test query
        total_queries = len(self.test_data["queries"])
        for i, test in enumerate(self.test_data["queries"], 1):
            print(f"\n[{i}/{total_queries}] Testing: {test['id']}")
            print(f"Query: {test['query'][:80]}...")
            
            # Run complete workflow
            result = self.run_complete_workflow(test["query"], test["id"])
            all_results["test_results"][test["id"]] = result
            
            # Collect events for validation CSV
            for event in result.get("final_events", []):
                # Handle both old and new event structures
                all_results["events_for_validation"].append({
                    "version": self.version,
                    "query_id": test["id"],
                    "event_title": event.get("title", "Unknown"),
                    "original_title": event.get("original_title", event.get("title", "")),
                    "event_date": str(event.get("date") or event.get("time", "")),
                    "event_location": event.get("location", ""),
                    "source_url": event.get("source_url", event.get("url", "")),
                    "has_basic_info": event.get("has_basic_info", False),
                    "is_past_event": event.get("is_past_event", False),
                    "score": event.get("recommendation", 0),
                    "rationale": event.get("rationale", ""),
                    "is_interesting": "",  # Manual validation
                    "validation_notes": ""  # Manual validation
                })
        
        # Calculate summary statistics
        all_results["summary"] = self.calculate_summary(all_results["test_results"])
        
        # Save all results
        self.save_results(all_results)
        
        # Print summary
        self.print_summary(all_results["summary"])
        
        return all_results
    
    def calculate_summary(self, test_results: Dict) -> Dict:
        """Calculate summary statistics across all tests."""
        
        summary = {
            "total_queries": len(test_results),
            "successful_queries": sum(1 for r in test_results.values() if "error" not in r),
            "total_candidates": 0,
            "total_extracted": 0,
            "total_scored": 0,
            "total_cycles": 0,
            "total_with_basic_info": 0,
            "total_api_cost": 0.0,
            "avg_candidates_per_query": 0,
            "avg_extracted_per_query": 0,
            "avg_scored_per_query": 0,
            "avg_cycles_per_query": 0,
            "avg_deduplication_rate": 0,  # v0.3.0
            "basic_info_percentage": 0
        }
        
        total_dedup_rate = 0
        queries_with_dedup = 0
        
        for result in test_results.values():
            if "error" not in result and "metrics" in result:
                metrics = result["metrics"]
                summary["total_candidates"] += metrics.get("total_candidates", 0)
                summary["total_extracted"] += metrics.get("total_extracted", 0)
                summary["total_scored"] += metrics.get("total_scored", 0)
                summary["total_cycles"] += metrics.get("cycles_performed", 0)
                summary["total_with_basic_info"] += metrics.get("events_with_basic_info", 0)
                summary["total_api_cost"] += metrics.get("total_cost", 0)
                
                # v0.3.0: Track deduplication
                if "pipeline_flow" in result:
                    dedup_rate = result["pipeline_flow"].get("deduplication_rate", 0)
                    if dedup_rate > 0:
                        total_dedup_rate += dedup_rate
                        queries_with_dedup += 1
        
        # Calculate averages
        if summary["successful_queries"] > 0:
            summary["avg_candidates_per_query"] = summary["total_candidates"] / summary["successful_queries"]
            summary["avg_extracted_per_query"] = summary["total_extracted"] / summary["successful_queries"]
            summary["avg_scored_per_query"] = summary["total_scored"] / summary["successful_queries"]
            summary["avg_cycles_per_query"] = summary["total_cycles"] / summary["successful_queries"]
            
            if summary["total_extracted"] > 0:
                summary["basic_info_percentage"] = (summary["total_with_basic_info"] / summary["total_extracted"]) * 100
            
            # v0.3.0: Average deduplication rate
            if queries_with_dedup > 0:
                summary["avg_deduplication_rate"] = total_dedup_rate / queries_with_dedup
        
        return summary
    
    def save_results(self, results: Dict):
        """Save benchmark results and validation CSV."""
        
        # Save full results as JSON
        results_file = self.results_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {results_file}")
        
        # Save validation CSV
        if results["events_for_validation"]:
            csv_file = self.results_dir / f"events_for_validation_{self.version}.csv"
            
            fieldnames = [
                "version", "query_id", "event_title", "original_title",
                "event_date", "event_location", "source_url",
                "has_basic_info", "is_past_event", "score", "rationale",
                "is_interesting", "validation_notes"
            ]
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results["events_for_validation"])
            
            print(f"Validation CSV saved to: {csv_file}")
            print(f"Total events for validation: {len(results['events_for_validation'])}")
    
    def print_summary(self, summary: Dict):
        """Print benchmark summary."""
        
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}\n")
        
        print("WORKFLOW METRICS:")
        print(f"  Successful queries: {summary['successful_queries']}/{summary['total_queries']}")
        print(f"  Avg candidates per query: {summary['avg_candidates_per_query']:.1f}")
        print(f"  Avg extracted per query: {summary['avg_extracted_per_query']:.1f}")
        print(f"  Avg scored per query: {summary['avg_scored_per_query']:.1f}")
        print(f"  Avg cycles per query: {summary['avg_cycles_per_query']:.1f}")
        
        print("\nQUALITY METRICS:")
        print(f"  Events with basic info: {summary['total_with_basic_info']}/{summary['total_extracted']} ({summary['basic_info_percentage']:.1f}%)")
        print(f"  Avg deduplication rate: {summary['avg_deduplication_rate']:.1f}%")
        
        print("\nCOST METRICS:")
        print(f"  Total API cost: ${summary['total_api_cost']:.4f}")
        print(f"  Avg cost per query: ${summary['total_api_cost']/summary['total_queries'] if summary['total_queries'] > 0 else 0:.4f}")
        
        print("\n📋 Manual validation required for 'is_interesting' column")


class BenchmarkComparator:
    """Compare benchmark results across versions."""
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """Compare two benchmark versions."""
        
        # Load results
        v1_file = Path(f"benchmarks/results/v{version1}/benchmark_results.json")
        v2_file = Path(f"benchmarks/results/v{version2}/benchmark_results.json")
        
        if not v1_file.exists() or not v2_file.exists():
            print(f"Error: Results not found for one or both versions")
            return {}
        
        with open(v1_file) as f:
            v1_results = json.load(f)
        with open(v2_file) as f:
            v2_results = json.load(f)
        
        # Compare summaries
        v1_summary = v1_results.get("summary", {})
        v2_summary = v2_results.get("summary", {})
        
        print(f"\n{'='*60}")
        print(f"COMPARISON: v{version1} → v{version2}")
        print(f"{'='*60}\n")
        
        # Key metrics comparison
        metrics = [
            ("Avg candidates/query", "avg_candidates_per_query", False),
            ("Avg extracted/query", "avg_extracted_per_query", True),
            ("Avg cycles/query", "avg_cycles_per_query", False),
            ("Basic info %", "basic_info_percentage", True),
            ("Total API cost", "total_api_cost", False)
        ]
        
        for label, key, higher_is_better in metrics:
            v1_val = v1_summary.get(key, 0)
            v2_val = v2_summary.get(key, 0)
            
            if v1_val > 0:
                change = ((v2_val - v1_val) / v1_val) * 100
                symbol = "↑" if v2_val > v1_val else "↓" if v2_val < v1_val else "="
                
                # Color coding (would work in terminal)
                if higher_is_better:
                    status = "✓" if v2_val > v1_val else "✗" if v2_val < v1_val else "="
                else:
                    status = "✓" if v2_val < v1_val else "✗" if v2_val > v1_val else "="
                
                if key == "total_api_cost":
                    print(f"{label:20} ${v1_val:.4f} → ${v2_val:.4f} ({change:+.1f}%) {symbol} {status}")
                elif "percentage" in key:
                    print(f"{label:20} {v1_val:.1f}% → {v2_val:.1f}% ({change:+.1f}%) {symbol} {status}")
                else:
                    print(f"{label:20} {v1_val:.1f} → {v2_val:.1f} ({change:+.1f}%) {symbol} {status}")
        
        # Load and compare validation results if available
        v1_csv = Path(f"benchmarks/results/v{version1}/events_for_validation_{version1}.csv")
        v2_csv = Path(f"benchmarks/results/v{version2}/events_for_validation_{version2}.csv")
        
        if v1_csv.exists() and v2_csv.exists():
            print("\n" + "="*60)
            print("VALIDATION COMPARISON (if manually validated)")
            print("="*60)
            
            # Count interesting events from CSV
            v1_interesting = self._count_interesting_events(v1_csv)
            v2_interesting = self._count_interesting_events(v2_csv)
            
            if v1_interesting is not None and v2_interesting is not None:
                v1_total = v1_interesting["total"]
                v2_total = v2_interesting["total"]
                v1_yes = v1_interesting["yes"]
                v2_yes = v2_interesting["yes"]
                
                if v1_total > 0 and v2_total > 0:
                    v1_pct = (v1_yes / v1_total) * 100
                    v2_pct = (v2_yes / v2_total) * 100
                    
                    print(f"Interesting events: {v1_yes}/{v1_total} ({v1_pct:.1f}%) → {v2_yes}/{v2_total} ({v2_pct:.1f}%)")
                    
                    if v1_pct > 0:
                        change = ((v2_pct - v1_pct) / v1_pct) * 100
                        print(f"Change: {change:+.1f}%")
            else:
                print("Manual validation not yet completed for one or both versions")
        
        return {
            "v1": v1_summary,
            "v2": v2_summary
        }
    
    def _count_interesting_events(self, csv_file: Path) -> Optional[Dict]:
        """Count interesting events from validation CSV."""
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                events = list(reader)
                
                total = len(events)
                yes_count = sum(1 for e in events if e.get("is_interesting", "").upper() == "YES")
                
                # Check if validation is complete
                validated = sum(1 for e in events if e.get("is_interesting", "").strip() != "")
                
                if validated < total * 0.5:  # Less than 50% validated
                    return None
                
                return {"total": total, "yes": yes_count, "validated": validated}
        except:
            return None


# Legacy compatibility classes for old run_benchmark.py
class VersionManager:
    """Legacy compatibility - now integrated into BenchmarkSystem."""
    def __init__(self):
        pass
    
    def create_version(self, version_num: str, description: str, changes: List[str]) -> Dict:
        benchmark = BenchmarkSystem(version_num)
        return benchmark.capture_version_info()


class BenchmarkRunner:
    """Legacy compatibility - now integrated into BenchmarkSystem."""
    def __init__(self, version: str):
        self.benchmark = BenchmarkSystem(version)
    
    def run_benchmark_suite(self) -> Dict:
        return self.benchmark.run_benchmark_suite()