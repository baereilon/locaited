"""Test Workflow v0.4.0 with ground truth events."""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.workflow_v4 import WorkflowV4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_workflow():
    """Test basic workflow with NYC events."""
    print("\n" + "="*60)
    print("TEST 1: Basic NYC Events Search")
    print("="*60)
    
    workflow = WorkflowV4(use_cache=True)
    
    user_input = {
        "location": "New York City",
        "time_frame": "this week",
        "interests": ["protests", "cultural events", "political events", "art exhibitions"]
    }
    
    print(f"Input: {user_input}")
    print("\nRunning workflow...")
    
    result = workflow.run_workflow(user_input)
    
    # Display results
    print("\n" + "-"*40)
    if result.get("gate_decision") == "APPROVE":
        events = result.get("events", [])
        print(f"✓ APPROVED - Found {len(events)} events\n")
        
        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event['title']}")
            print(f"   Date: {event.get('date', 'TBD')}")
            print(f"   Location: {event.get('location', 'TBD')}")
            print(f"   Access: {event.get('access_req', 'Unknown')}")
            print(f"   Score: {event.get('score', 'N/A')}")
            print()
    else:
        print(f"✗ {result.get('gate_decision')}")
        if result.get('feedback'):
            print(f"Feedback: {result['feedback']}")
    
    # Show metrics
    if "workflow_metrics" in result:
        metrics = result["workflow_metrics"]
        print("-"*40)
        print("Metrics:")
        print(f"  Cost: ${metrics['total_cost']:.4f}")
        print(f"  Duration: {metrics['total_duration_seconds']:.1f}s")
        print(f"  Iterations: {metrics['iterations']}")
        print(f"  Leads generated: {metrics['leads_generated']}")
        print(f"  Evidence found: {metrics['evidence_found']}")
        print(f"  Events extracted: {metrics['events_extracted']}")
    
    return result


def test_specific_interest():
    """Test with specific interest focus."""
    print("\n" + "="*60)
    print("TEST 2: Specific Interest - Climate Protests")
    print("="*60)
    
    workflow = WorkflowV4(use_cache=True)
    workflow.reset_metrics()  # Clean metrics from previous test
    
    user_input = {
        "location": "New York City",
        "time_frame": "this week",
        "interests": ["climate protests", "environmental activism", "Extinction Rebellion"]
    }
    
    print(f"Input: {user_input}")
    print("\nRunning workflow...")
    
    result = workflow.run_workflow(user_input)
    
    # Display results
    print("\n" + "-"*40)
    if result.get("gate_decision") == "APPROVE":
        events = result.get("events", [])
        print(f"✓ APPROVED - Found {len(events)} events\n")
        
        # Check if we found climate-related events
        climate_events = [e for e in events if any(
            keyword in e.get('title', '').lower() + e.get('description', '').lower()
            for keyword in ['climate', 'environment', 'extinction', 'green']
        )]
        
        print(f"Climate-related events: {len(climate_events)}/{len(events)}")
        
        for event in climate_events[:3]:
            print(f"\n- {event['title']}")
            print(f"  {event.get('description', '')[:100]}...")
    else:
        print(f"✗ {result.get('gate_decision')}")
        if result.get('feedback'):
            print(f"Feedback: {result['feedback']}")
    
    return result


def test_vague_request():
    """Test with vague user request to see if Editor handles it well."""
    print("\n" + "="*60)
    print("TEST 3: Vague Request")
    print("="*60)
    
    workflow = WorkflowV4(use_cache=True)
    workflow.reset_metrics()
    
    # Intentionally vague
    user_input = {
        "location": "NYC",
        "time_frame": "soon",
        "interests": ["interesting stuff"]
    }
    
    print(f"Input: {user_input}")
    print("\nRunning workflow...")
    
    result = workflow.run_workflow(user_input)
    
    # Display what the Editor interpreted
    profile = result.get("profile", {})
    print("\n" + "-"*40)
    print("Editor interpretation:")
    print(f"  Location: {profile.get('location')}")
    print(f"  Time frame: {profile.get('time_frame')}")
    print(f"  Focus areas: {profile.get('focus_event_types', [])[:3]}")
    print(f"  Guidance: {profile.get('researcher_guidance', '')[:150]}...")
    
    print("\n" + "-"*40)
    if result.get("gate_decision") == "APPROVE":
        events = result.get("events", [])
        print(f"✓ APPROVED - Found {len(events)} events despite vague request")
    else:
        print(f"✗ {result.get('gate_decision')}")
    
    return result


def save_test_results(results):
    """Save test results to file."""
    output_file = Path("test_results_v4.json")
    
    # Prepare summary
    summary = {
        "test_date": datetime.now().isoformat(),
        "version": "v0.4.0",
        "tests": []
    }
    
    for test_name, result in results.items():
        test_summary = {
            "test": test_name,
            "gate_decision": result.get("gate_decision"),
            "events_found": len(result.get("events", [])),
            "iterations": result.get("workflow_metrics", {}).get("iterations", 0),
            "total_cost": result.get("workflow_metrics", {}).get("total_cost", 0),
            "duration": result.get("workflow_metrics", {}).get("total_duration_seconds", 0)
        }
        
        # Add sample events
        if result.get("events"):
            test_summary["sample_events"] = [
                {
                    "title": e["title"],
                    "date": e.get("date"),
                    "score": e.get("score")
                }
                for e in result["events"][:3]
            ]
        
        summary["tests"].append(test_summary)
    
    # Calculate totals
    summary["totals"] = {
        "total_cost": sum(t["total_cost"] for t in summary["tests"]),
        "total_events": sum(t["events_found"] for t in summary["tests"]),
        "success_rate": sum(1 for t in summary["tests"] if t["gate_decision"] == "APPROVE") / len(summary["tests"])
    }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n\nResults saved to {output_file}")
    return summary


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING WORKFLOW v0.4.0 WITH GROUND TRUTH")
    print("="*60)
    
    results = {}
    
    # Run tests
    try:
        results["basic"] = test_basic_workflow()
    except Exception as e:
        logger.error(f"Basic test failed: {e}")
        results["basic"] = {"gate_decision": "ERROR", "error": str(e)}
    
    try:
        results["specific"] = test_specific_interest()
    except Exception as e:
        logger.error(f"Specific interest test failed: {e}")
        results["specific"] = {"gate_decision": "ERROR", "error": str(e)}
    
    try:
        results["vague"] = test_vague_request()
    except Exception as e:
        logger.error(f"Vague request test failed: {e}")
        results["vague"] = {"gate_decision": "ERROR", "error": str(e)}
    
    # Save and display summary
    summary = save_test_results(results)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Success rate: {summary['totals']['success_rate']:.0%}")
    print(f"Total events found: {summary['totals']['total_events']}")
    print(f"Total cost: ${summary['totals']['total_cost']:.4f}")
    
    print("\n✓ Testing complete!")


if __name__ == "__main__":
    main()