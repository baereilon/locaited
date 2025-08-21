"""Simple benchmark focusing on September events to match test data."""

import logging
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from src.agents.workflow import Workflow

logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(levelname)s - %(message)s'
)

def load_september_events() -> List[Dict[str, Any]]:
    """Load test events happening in September 2025."""
    df = pd.read_csv("test_data/Liri Interesting events.csv")
    
    september_events = []
    for _, row in df.iterrows():
        if pd.notna(row.get('event')) and pd.notna(row.get('date')):
            date_str = str(row['date']).strip()
            # Look for September events
            if 'Sep' in date_str:
                september_events.append({
                    'title': str(row['event']).strip(),
                    'date': date_str,
                    'type': str(row.get('type', '')).strip() if pd.notna(row.get('type')) else '',
                    'location': str(row.get('Location', '')).strip() if pd.notna(row.get('Location')) else ''
                })
    
    return september_events

def simple_match(found_events: List[Dict], test_events: List[Dict]) -> List[Dict]:
    """Simple matching based on key words."""
    matches = []
    
    for found in found_events:
        found_title = found.get('title', '').lower()
        for test in test_events:
            test_title = test['title'].lower()
            
            # Check for key distinctive words
            if 'mtv' in found_title and 'mtv' in test_title:
                matches.append({'found': found['title'], 'test': test['title'], 'match_type': 'MTV Awards'})
            elif 'un' in found_title and ('un' in test_title or 'general assembly' in test_title.lower()):
                matches.append({'found': found['title'], 'test': test['title'], 'match_type': 'UN Event'})
            elif 'fashion' in found_title and 'fashion' in test_title:
                matches.append({'found': found['title'], 'test': test['title'], 'match_type': 'Fashion Week'})
    
    return matches

def run_simple_benchmark():
    """Run focused benchmark on September events."""
    
    print("=" * 80)
    print("SIMPLE BENCHMARK - September 2025 Events")
    print("=" * 80)
    
    # Load September test events
    test_events = load_september_events()
    print(f"\nTest Events in September 2025:")
    for event in test_events:
        print(f"  - {event['title']} ({event['date']})")
    
    # Initialize workflow without cache
    print("\nInitializing workflow...")
    workflow = Workflow(use_cache=False)
    
    # Single focused query for September
    test_input = {
        "location": "New York City",
        "time_frame": "September 2025",
        "interests": ["MTV awards", "UN General Assembly", "Fashion Week", "cultural events", "political events"]
    }
    
    print(f"\nRunning query: {test_input}")
    print("-" * 80)
    
    try:
        # Run workflow
        start_time = datetime.now()
        result = workflow.run_workflow(test_input)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extract results
        gate_decision = result.get('gate_decision')
        events_found = result.get('events', [])
        metrics = result.get('workflow_metrics', {})
        
        print(f"\nResults:")
        print(f"  Gate Decision: {gate_decision}")
        print(f"  Events Found: {len(events_found)}")
        print(f"  Total Cost: ${metrics.get('total_cost', 0):.4f}")
        print(f"  Duration: {duration:.1f}s")
        
        # Check for matches
        if events_found:
            matches = simple_match(events_found, test_events)
            
            print(f"\nMatches Found: {len(matches)}")
            for match in matches:
                print(f"  ✓ {match['match_type']}")
                print(f"    Found: {match['found'][:60]}...")
                print(f"    Test:  {match['test'][:60]}...")
            
            # Show all found events
            print(f"\nAll Found Events ({len(events_found)}):")
            for i, event in enumerate(events_found, 1):
                print(f"  {i}. {event.get('title', 'No title')[:70]}...")
                print(f"     Date: {event.get('date', 'No date')}, Score: {event.get('score', 'N/A')}")
        
        # Save results
        with open('benchmark_simple_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'query': test_input,
                'gate_decision': gate_decision,
                'events_found': len(events_found),
                'matches': len(matches) if events_found else 0,
                'cost': metrics.get('total_cost', 0),
                'duration': duration,
                'found_events': events_found[:5]  # Save sample
            }, f, indent=2)
        
        print("\nResults saved to benchmark_simple_results.json")
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        if gate_decision == "APPROVE":
            print("✓ Workflow approved events")
        else:
            print(f"✗ Workflow status: {gate_decision}")
            
        if len(events_found) <= 15:
            print(f"✓ Event count reasonable ({len(events_found)} ≤ 15)")
        else:
            print(f"⚠ Too many events returned ({len(events_found)} > 15)")
            
        if metrics.get('total_cost', 0) < 0.05:
            print(f"✓ Cost efficient (${metrics.get('total_cost', 0):.4f} < $0.05)")
        else:
            print(f"⚠ High cost (${metrics.get('total_cost', 0):.4f})")
            
        if duration < 180:
            print(f"✓ Fast execution ({duration:.1f}s < 180s)")
        else:
            print(f"⚠ Slow execution ({duration:.1f}s)")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_benchmark()