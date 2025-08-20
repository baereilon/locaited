"""Test single workflow run."""

import logging
from src.agents.workflow_v4 import WorkflowV4

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

workflow = WorkflowV4()

# Simple test case
test_input = {
    "location": "New York City",
    "time_frame": "this week",
    "interests": ["protests", "cultural events"]
}

print(f"Testing: {test_input}")
result = workflow.run_workflow(test_input)

print(f"\nGate Decision: {result.get('gate_decision')}")
print(f"Events Found: {len(result.get('events', []))}")

# Get cost from workflow_metrics
metrics = result.get('workflow_metrics', {})
print(f"Total Cost: ${metrics.get('total_cost', 0):.4f}")

if result.get('events'):
    print("\nTop Events:")
    for i, event in enumerate(result['events'][:3], 1):
        print(f"{i}. {event.get('title', 'No title')}")
        print(f"   Date: {event.get('date', 'No date')}")
        print(f"   Location: {event.get('location', 'No location')}")
elif result.get('error'):
    print(f"\nError: {result['error']}")
elif result.get('feedback'):
    print(f"\nFeedback: {result['feedback']}")