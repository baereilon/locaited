"""Validation script for LocAIted workflow - generates CSV output for manual review.

This is the primary validation tool for assessing the north star metrics:
1. Number of interesting events (manual assessment)
2. Number of events with complete basic info
3. Number of duplicate events

Outputs:
- Main CSV matching v0.3.0 format for manual validation
- Agent visibility CSV for deep dive analysis
- Metadata JSON with run statistics
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.agents.workflow import Workflow

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)

def assess_completeness(event: Dict[str, Any]) -> Tuple[bool, bool, str]:
    """Check if event has all basic required information.
    
    Returns:
        (has_basic_info, has_time, missing_fields)
    """
    has_title = bool(event.get('title') and len(event.get('title', '')) > 10)
    has_date = bool(event.get('date') and str(event.get('date')) not in ['null', 'None', ''])
    has_time = bool(event.get('time') and str(event.get('time')) not in ['null', 'None', ''])
    has_location = bool(event.get('location') and len(event.get('location', '')) > 10)
    
    has_basic_info = all([has_title, has_date, has_time, has_location])
    
    missing = []
    if not has_title: missing.append('title')
    if not has_date: missing.append('date')
    if not has_time: missing.append('time')
    if not has_location: missing.append('location')
    
    return has_basic_info, has_time, ', '.join(missing)

def create_main_validation_csv(events: List[Dict], output_dir: str, timestamp: str) -> str:
    """Create main validation CSV matching v0.3.0 format."""
    
    csv_filepath = os.path.join(output_dir, f"events_for_validation_0.4.0_{timestamp}.csv")
    
    with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'version', 'query_id', 'event_title', 'original_title', 'event_date', 
            'event_time', 'event_location', 'source_url', 'has_basic_info', 
            'has_time', 'is_past_event', 'score', 'publisher_rank', 'rationale',
            'is_interesting', 'validation_notes'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, event in enumerate(events, 1):
            has_basic_info, has_time, missing = assess_completeness(event)
            
            writer.writerow({
                'version': '0.4.0',
                'query_id': 'standard_validation',
                'event_title': event.get('title', 'NO TITLE'),
                'original_title': event.get('title', ''),
                'event_date': event.get('date', ''),
                'event_time': event.get('time', ''),
                'event_location': event.get('location', ''),
                'source_url': event.get('url', ''),
                'has_basic_info': str(has_basic_info).upper(),
                'has_time': str(has_time).upper(),
                'is_past_event': 'FALSE',  # All should be future for "next 2 weeks"
                'score': event.get('score', 0),
                'publisher_rank': i,
                'rationale': event.get('description', '')[:200],
                'is_interesting': '',  # For manual assessment
                'validation_notes': f'Missing: {missing}' if missing else ''
            })
    
    return csv_filepath

def create_agent_visibility_csv(result: Dict, output_dir: str, timestamp: str) -> str:
    """Create CSV showing agent outputs for deep dive analysis."""
    
    leads = result.get('leads', [])
    evidence = result.get('evidence', [])
    events = result.get('events', [])
    
    filepath = os.path.join(output_dir, f"agent_outputs_0.4.0_{timestamp}.csv")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'lead_index', 'lead_description', 'lead_type', 'lead_keywords',
            'evidence_found', 'evidence_count', 'evidence_sample',
            'became_event', 'event_title', 'event_score', 'in_top_10'
        ])
        
        # Process each lead
        for i, lead in enumerate(leads[:25], 1):
            # Find corresponding evidence
            ev = evidence[i-1] if i <= len(evidence) else {}
            evidence_found = 'Yes' if ev.get('results') else 'No'
            evidence_count = len(ev.get('results', []))
            evidence_sample = (ev.get('answer', '')[:100] + '...') if ev.get('answer') else ''
            
            # Try to match to final event (simple keyword matching)
            matched_event = None
            for event in events:
                lead_keywords = ' '.join(lead.get('keywords', [])).lower()
                event_title = event.get('title', '').lower()
                if lead_keywords and any(kw in event_title for kw in lead_keywords.split()[:3]):
                    matched_event = event
                    break
            
            writer.writerow([
                i,
                lead.get('description', '')[:100],
                lead.get('type', ''),
                ', '.join(lead.get('keywords', []))[:50],
                evidence_found,
                evidence_count,
                evidence_sample,
                'Yes' if matched_event else 'No',
                matched_event.get('title', '')[:100] if matched_event else '',
                matched_event.get('score', '') if matched_event else '',
                'Yes' if matched_event and events.index(matched_event) < 10 else 'No'
            ])
    
    return filepath

def run_validation(use_cache: bool = False):
    """Run workflow and generate CSV validation outputs."""
    
    print("=" * 80)
    print("LOCAITED VALIDATION - CSV Output for Manual Review")
    print("=" * 80)
    
    workflow = Workflow(use_cache=use_cache)
    
    # Standard test query
    query = {
        "location": "New York City",
        "time_frame": "next 2 weeks",
        "interests": ["protests", "cultural events", "political events", "parades", "art exhibitions"]
    }
    
    print(f"\nQuery: {query}")
    print("Running workflow...\n")
    
    # Run workflow
    start = datetime.now()
    result = workflow.run_workflow(query)
    duration = (datetime.now() - start).total_seconds()
    
    # Extract results
    events = result.get('events', [])
    metrics = result.get('workflow_metrics', {})
    
    # Set up output directory
    output_dir = "benchmarks/results/v0.4.0"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamp for file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate CSV files
    main_csv = create_main_validation_csv(events, output_dir, timestamp)
    agent_csv = create_agent_visibility_csv(result, output_dir, timestamp)
    
    # Create metadata JSON for run statistics
    metadata_filepath = os.path.join(output_dir, f"run_metadata_{timestamp}.json")
    with open(metadata_filepath, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'duration_seconds': duration,
            'total_cost': metrics.get('total_cost', 0),
            'gate_decision': result.get('gate_decision'),
            'total_events': len(events),
            'events_with_complete_info': sum(1 for e in events if assess_completeness(e)[0]),
            'events_with_time': sum(1 for e in events if assess_completeness(e)[1]),
            'workflow_iterations': metrics.get('iterations', 1),
            'files': {
                'main_validation': os.path.basename(main_csv),
                'agent_visibility': os.path.basename(agent_csv)
            }
        }, f, indent=2)
    
    # Print summary
    complete_count = sum(1 for e in events if assess_completeness(e)[0])
    time_count = sum(1 for e in events if assess_completeness(e)[1])
    
    print("SUMMARY")
    print("-" * 40)
    print(f"Total Events Found: {len(events)}")
    print(f"Events with Complete Info: {complete_count}/{len(events)}")
    print(f"Events with Time: {time_count}/{len(events)}")
    print(f"Duration: {duration:.1f}s")
    print(f"Cost: ${metrics.get('total_cost', 0):.4f}")
    print(f"Gate Decision: {result.get('gate_decision')}")
    
    # Print sample events
    print("\nSAMPLE EVENTS (First 3):")
    for i, event in enumerate(events[:3], 1):
        has_basic, has_time, missing = assess_completeness(event)
        print(f"\n{i}. {event.get('title', 'NO TITLE')[:60]}")
        print(f"   Date: {event.get('date', 'NO DATE')}, Time: {event.get('time', 'NO TIME')}")
        print(f"   Location: {event.get('location', 'NO LOCATION')[:50]}")
        print(f"   Complete: {'✓' if has_basic else '✗'} {f'(Missing: {missing})' if missing else ''}")
    
    print(f"\n{'=' * 80}")
    print("FILES GENERATED:")
    print(f"1. Main validation CSV: {main_csv}")
    print(f"2. Agent visibility CSV: {agent_csv}")
    print(f"3. Run metadata JSON: {metadata_filepath}")
    print("\nMANUAL VALIDATION STEPS:")
    print("1. Open the main CSV in Excel/Google Sheets")
    print("2. Review each event and mark 'is_interesting' column (Yes/No)")
    print("3. Check for duplicate events and note in 'validation_notes'")
    print("4. Verify location specificity for photographer navigation")
    print("5. Use agent visibility CSV to understand pipeline flow if needed")
    
    return main_csv

if __name__ == "__main__":
    run_validation(use_cache=False)