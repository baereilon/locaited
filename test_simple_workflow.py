"""Simple workflow test - one pass through all agents without cycles."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent

def test_simple_workflow():
    """Test all agents in sequence without LangGraph complexity."""
    
    print("=" * 60)
    print("SIMPLE WORKFLOW TEST - ALL AGENTS SEQUENTIALLY")
    print("=" * 60)
    
    # 1. The Editor
    print("\n1. PROFILE & PLANNER AGENT")
    print("-" * 40)
    editor = EditorAgent()
    user_profile = editor.build_user_profile()
    
    print(f"Built profile:")
    print(f"  - {len(user_profile['allowlist_domains'])} domains")
    print(f"  - {len(user_profile['keywords'])} keywords")
    print(f"  - Interest areas: {user_profile['interest_areas']}")
    print(f"  - Credentials: {user_profile['credentials']}")
    
    # 2. Retriever
    print("\n2. RETRIEVER AGENT")
    print("-" * 40)
    researcher_agent = ResearcherAgent()
    
    query = "Find upcoming protests, political events, and cultural activities"
    print(f"Query: {query}")
    print("Calling Tavily Search API...")
    
    candidates = researcher_agent.search_events(
        query=query,
        keywords=user_profile['keywords'][:10],
        domains=user_profile['allowlist_domains'][:10],
        location="NYC",
        max_results=10
    )
    
    print(f"Found {len(candidates)} candidates")
    
    if candidates:
        # Re-rank by relevance
        candidates = researcher_agent.re_rank_by_relevance(
            candidates,
            user_profile['interest_areas'],
            user_profile['keywords']
        )
        
        print("\nTop 3 candidates:")
        for i, c in enumerate(candidates[:3], 1):
            print(f"  {i}. {c.get('title', 'No title')}")
            print(f"     Score: {c.get('score', 0):.2f}")
            print(f"     URL: {c['url']}")
    
    # 3. Extractor
    print("\n3. EXTRACTOR AGENT")
    print("-" * 40)
    
    if not candidates:
        print("No candidates to extract")
        return
    
    fact_checker_agent = FactCheckerAgent()
    
    # Extract top 2 URLs
    urls_to_extract = [c["url"] for c in candidates[:2]]
    print(f"Extracting {len(urls_to_extract)} URLs with Tavily Extract API...")
    
    # Use the batch extraction method
    print(f"Extracting {len(candidates[:2])} candidates...")
    try:
        extracted_events = fact_checker_agent.extract_from_candidates(
            candidates[:2],
            max_extractions=2
        )
        print(f"  ✓ Successfully extracted {len(extracted_events)} events")
        for event in extracted_events:
            print(f"    - {event['title']}")
    except Exception as e:
        print(f"  ✗ Extraction failed: {str(e)}")
        extracted_events = []
    
    print(f"\nTotal extracted: {len(extracted_events)} events")
    
    # 4. Recommender
    print("\n4. RECOMMENDER AGENT")
    print("-" * 40)
    
    if not extracted_events:
        print("No events to score")
        return
    
    publisher_agent = PublisherAgent()
    
    print(f"Scoring {len(extracted_events)} events with OpenAI API...")
    
    result = publisher_agent.score_and_rank(
        events=extracted_events,
        user_profile=user_profile,
        cycle_count=0
    )
    
    print(f"\nScoring complete:")
    print(f"  - API cost: ${result['cost']:.6f}")
    print(f"  - Viable events: {result['stats']['viable_events']}")
    print(f"  - Decision: {result['decision']['action']}")
    print(f"  - Notes: {result['decision']['notes']}")
    
    if result['top10']:
        print(f"\nTop Recommendations:")
        for i, event in enumerate(result['top10'][:3], 1):
            print(f"\n{i}. {event['title']}")
            print(f"   Score: {event['recommendation']:.2f}")
            print(f"   Location: {event['location']}")
            print(f"   Rationale: {event['rationale']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Profile domains: {len(user_profile['allowlist_domains'])}")
    print(f"Search results: {len(candidates)}")
    print(f"Extracted events: {len(extracted_events)}")
    print(f"Recommendations: {len(result.get('top10', []))}")
    print(f"Total API cost: ~${0.01 + len(urls_to_extract)*0.01 + result['cost']:.4f}")
    
    print("\n✅ Simple workflow test complete!")
    print("Check extraction_results/ and recommendation_results/ for details")

if __name__ == "__main__":
    print("\n⚠️  API USAGE WARNING")
    print("This test will use:")
    print("  - 1 Tavily search credit")
    print("  - 2 Tavily extract credits")
    print("  - ~$0.0002 OpenAI credits")
    print("\nProceeding automatically...")
    print()
    
    test_simple_workflow()