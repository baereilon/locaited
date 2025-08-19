#!/usr/bin/env python
"""Script to update all agent names to newsroom metaphor."""

import os
import re
from pathlib import Path

# Define replacements
replacements = {
    # Class names
    "ProfilePlannerAgent": "EditorAgent",
    "RetrieverAgent": "ResearcherAgent", 
    "ExtractorAgent": "FactCheckerAgent",
    "RecommenderAgent": "PublisherAgent",
    
    # Import statements
    "from agents.profile_planner": "from agents.editor",
    "from agents.retriever": "from agents.researcher",
    "from agents.extractor": "from agents.fact_checker",
    "from agents.recommender": "from agents.publisher",
    
    # Variable names (common patterns)
    "profile_agent": "editor",
    "retriever": "researcher",
    "extractor": "fact_checker",
    "recommender": "publisher",
    
    # Test function names
    "test_profile_planner": "test_editor",
    "test_retriever": "test_researcher",
    "test_extractor": "test_fact_checker",
    "test_recommender": "test_publisher",
    
    # Comments and docstrings
    "Profile & Planner": "The Editor",
    "Retriever agent": "The Researcher",
    "Extractor agent": "The Fact-Checker",
    "Recommender agent": "The Publisher",
    "Profile and Planner": "The Editor",
    "retriever agent": "researcher",
    "extractor agent": "fact-checker",
    "recommender agent": "publisher"
}

def update_file(filepath):
    """Update a single file with replacements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Updated: {}".format(filepath))
            return True
        return False
    except Exception as e:
        print("Error updating {}: {}".format(filepath, e))
        return False

def main():
    """Update all relevant files."""
    files_to_update = [
        # Agent files
        "src/agents/researcher.py",
        "src/agents/fact_checker.py", 
        "src/agents/publisher.py",
        "src/agents/workflow.py",
        
        # API and test files
        "src/api.py",
        "test_simple_workflow.py",
        "test_complete_workflow.py",
        
        # Benchmark files
        "benchmarks/benchmark_system.py",
        "run_benchmark.py"
    ]
    
    updated = 0
    for filepath in files_to_update:
        full_path = Path(filepath)
        if full_path.exists():
            if update_file(full_path):
                updated += 1
        else:
            print("File not found: {}".format(filepath))
    
    print("\n" + "="*50)
    print("Updated {} files with newsroom metaphor".format(updated))
    print("="*50)

if __name__ == "__main__":
    main()