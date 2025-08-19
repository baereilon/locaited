"""Complete workflow test for LocAIted - integrating all real agents."""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent

class QuerySpec(TypedDict):
    """User query specification."""
    text: str
    city: str
    date_from: datetime
    date_to: datetime
    model: str
    version: str

class UserProfile(TypedDict):
    """User profile for search customization."""
    allowlist_domains: List[str]
    keywords: List[str]
    prior_feedback: List[Dict[str, Any]]
    interest_areas: List[str]
    credentials: List[str]
    location_preference: str

class Candidate(TypedDict):
    """Search result candidate."""
    url: str
    title: Optional[str]
    snippet: str
    score: float

class ExtractedEvent(TypedDict):
    """Normalized event data."""
    title: str
    time: Optional[datetime]
    location: str
    organizer: str
    url: str
    access_req: str
    summary: Optional[str]

class Decision(TypedDict):
    """Gate decision for cycle control."""
    action: Literal["revise", "accept"]
    notes: str

class WorkflowState(TypedDict):
    """Complete state for the LangGraph workflow."""
    query_spec: QuerySpec
    user_profile: UserProfile
    candidates: List[Candidate]
    extracted: List[ExtractedEvent]
    top10: List[Dict[str, Any]]
    decision: Decision
    cycle_count: int
    total_cost: float
    errors: List[str]
    logs: List[str]

def profile_planner_node(state: WorkflowState) -> WorkflowState:
    """The Editor agent node with real data."""
    state["logs"].append("The Editor: Building search profile from test data")
    
    agent = EditorAgent()
    
    if not state.get("user_profile") or len(state["user_profile"]) == 0:
        profile = agent.build_user_profile()
        
        state["user_profile"] = {
            "allowlist_domains": list(profile["allowlist_domains"]),
            "keywords": profile["keywords"],
            "prior_feedback": profile["prior_feedback"],
            "interest_areas": profile["interest_areas"],
            "credentials": profile["credentials"],
            "location_preference": profile["location_preference"]
        }
        
        state["logs"].append(f"Profile: {len(profile['allowlist_domains'])} domains, {len(profile['keywords'])} keywords")
    
    if state.get("decision", {}).get("action") == "revise":
        state["logs"].append(f"Profile: Revising - {state['decision']['notes']}")
        if "expand" in state["decision"]["notes"].lower():
            current_domains = state["user_profile"]["allowlist_domains"]
            if len(current_domains) < 20:
                expanded = list(agent.extract_domains_from_events())
                state["user_profile"]["allowlist_domains"] = expanded[:20]
                state["logs"].append(f"Profile: Expanded to {len(state['user_profile']['allowlist_domains'])} domains")
    
    return state

def researcher_node(state: WorkflowState) -> WorkflowState:
    """The Researcher node with real Tavily API."""
    state["logs"].append("Retriever: Searching with Tavily API")
    
    agent = ResearcherAgent()
    
    query_spec = state.get("query_spec", {})
    user_profile = state.get("user_profile", {})
    
    try:
        candidates = agent.search_events(
            query=query_spec.get("text", "events in NYC"),
            keywords=user_profile.get("keywords", []),
            domains=user_profile.get("allowlist_domains", []),
            location=query_spec.get("city", "NYC"),
            date_from=query_spec.get("date_from"),
            date_to=query_spec.get("date_to"),
            max_results=10
        )
        
        if candidates:
            candidates = agent.re_rank_by_relevance(
                candidates,
                user_profile.get("interest_areas", []),
                user_profile.get("keywords", [])
            )
        
        state["candidates"] = candidates
        state["logs"].append(f"Retriever: Found {len(candidates)} candidates")
        state["total_cost"] = state.get("total_cost", 0) + 0.01
        
    except Exception as e:
        state["logs"].append(f"Retriever: Error - {str(e)}")
        state["errors"].append(f"Retriever error: {str(e)}")
        state["candidates"] = []
    
    return state

def fact_checker_node(state: WorkflowState) -> WorkflowState:
    """The Fact-Checker node with real Tavily Extract API."""
    num_candidates = len(state['candidates'])
    state["logs"].append(f"Extractor: Processing {num_candidates} candidates")
    
    if num_candidates == 0:
        state["extracted"] = []
        return state
    
    agent = FactCheckerAgent()
    
    urls_to_extract = [c["url"] for c in state["candidates"][:3]]
    
    print(f"\nWARNING: About to call Tavily Extract API for {len(urls_to_extract)} URLs")
    print(f"This will use {len(urls_to_extract)} extract credits")
    
    extracted_events = []
    for url in urls_to_extract:
        try:
            event = agent.extract_event(
                url=url,
                title=next((c.get("title", "Unknown") for c in state["candidates"] if c["url"] == url), "Unknown"),
                score=next((c.get("score", 0.5) for c in state["candidates"] if c["url"] == url), 0.5)
            )
            extracted_events.append(event)
        except Exception as e:
            state["logs"].append(f"Extractor: Failed for {url}: {str(e)}")
    
    state["extracted"] = extracted_events
    state["total_cost"] = state.get("total_cost", 0) + (len(urls_to_extract) * 0.01)
    state["logs"].append(f"Extractor: Extracted {len(extracted_events)} events")
    
    return state

def publisher_gate_node(state: WorkflowState) -> WorkflowState:
    """Recommender/Gate agent node with real LLM scoring."""
    num_events = len(state['extracted'])
    state["logs"].append(f"Recommender: Scoring {num_events} events")
    
    # Increment cycle count before decision
    state["cycle_count"] = state.get("cycle_count", 0) + 1
    
    if num_events == 0:
        state["top10"] = []
        state["decision"] = {
            "action": "accept",  # Always accept if no events after trying
            "notes": "No events to score"
        }
        return state
    
    agent = PublisherAgent()
    
    print(f"\nWARNING: About to call OpenAI API to score {num_events} events")
    print(f"Estimated cost: ~$0.0002")
    
    result = agent.score_and_rank(
        events=state["extracted"],
        user_profile=state["user_profile"],
        cycle_count=state.get("cycle_count", 0)
    )
    
    state["top10"] = result["top10"]
    state["decision"] = result["decision"]
    state["total_cost"] = state.get("total_cost", 0) + result.get("cost", 0)
    
    state["logs"].append(f"Recommender: {result['decision']['action']} - {result['decision']['notes']}")
    
    return state

def should_continue(state: WorkflowState) -> str:
    """Determine whether to continue the cycle or finish."""
    if state["decision"]["action"] == "revise" and state.get("cycle_count", 0) < 2:
        return "profile_planner"
    else:
        return "end"

def create_workflow() -> StateGraph:
    """Create the complete LangGraph workflow."""
    
    workflow = StateGraph(WorkflowState)
    
    workflow.add_node("profile_planner", profile_planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("publisher_gate", publisher_gate_node)
    
    workflow.add_edge("profile_planner", "researcher")
    workflow.add_edge("researcher", "fact_checker")
    workflow.add_edge("fact_checker", "publisher_gate")
    
    workflow.add_conditional_edges(
        "publisher_gate",
        should_continue,
        {
            "profile_planner": "profile_planner",
            "end": END
        }
    )
    
    workflow.set_entry_point("profile_planner")
    
    return workflow.compile()

def run_complete_workflow_test():
    """Run the complete workflow with all real agents."""
    print("=" * 60)
    print("COMPLETE WORKFLOW TEST - ALL AGENTS INTEGRATED")
    print("=" * 60)
    
    initial_state = {
        "query_spec": {
            "text": "Find upcoming protests, political events, and cultural activities",
            "city": "NYC",
            "date_from": datetime.now(),
            "date_to": datetime.now() + timedelta(days=30),
            "model": "gpt-3.5-turbo",
            "version": "1.0"
        },
        "user_profile": {},
        "candidates": [],
        "extracted": [],
        "top10": [],
        "decision": {"action": "accept", "notes": ""},
        "cycle_count": 0,
        "total_cost": 0.0,
        "errors": [],
        "logs": []
    }
    
    print("\nQuery Details:")
    print(f"  Text: {initial_state['query_spec']['text']}")
    print(f"  City: {initial_state['query_spec']['city']}")
    print(f"  Date Range: {initial_state['query_spec']['date_from'].date()} to {initial_state['query_spec']['date_to'].date()}")
    
    print("\n" + "=" * 60)
    print("API CREDIT WARNING")
    print("=" * 60)
    print("This test will use:")
    print("  - 1 Tavily search credit")
    print("  - 2-3 Tavily extract credits")
    print("  - ~$0.0002 OpenAI credits")
    print("\nTotal estimated cost: ~$0.04")
    print("=" * 60)
    
    print("\nProceeding with test (auto-approved for testing)...")
    
    app = create_workflow()
    
    print("\n" + "=" * 60)
    print("EXECUTING WORKFLOW...")
    print("=" * 60)
    
    # Set recursion limit to prevent infinite loops
    config = {"recursion_limit": 3}
    result = app.invoke(initial_state, config=config)
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    
    print(f"\nWorkflow Stats:")
    print(f"  Cycles: {result['cycle_count']}")
    print(f"  Total Cost: ${result['total_cost']:.4f}")
    print(f"  Candidates Found: {len(result['candidates'])}")
    print(f"  Events Extracted: {len(result['extracted'])}")
    print(f"  Recommendations: {len(result['top10'])}")
    
    if result['top10']:
        print(f"\nTop Recommendations:")
        for i, event in enumerate(result['top10'][:5], 1):
            print(f"\n{i}. {event.get('title', 'Unknown')}")
            print(f"   Score: {event.get('recommendation', 0):.2f}")
            print(f"   Location: {event.get('location', 'Unknown')}")
            print(f"   Access: {event.get('access_req', 'Unknown')}")
            if 'rationale' in event:
                print(f"   Rationale: {event['rationale']}")
            print(f"   URL: {event.get('url', 'N/A')}")
    
    print("\nWorkflow Logs:")
    for log in result['logs']:
        print(f"  • {log}")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  ⚠️ {error}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print(f"Check extraction_results/ and recommendation_results/ for details")
    print("=" * 60)

if __name__ == "__main__":
    run_complete_workflow_test()