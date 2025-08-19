"""LangGraph workflow for LocAIted multi-agent system."""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage

# Import the agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent

# State definitions based on the agent architecture document

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

# Main workflow state
class WorkflowState(TypedDict):
    """Complete state for the LangGraph workflow."""
    # Input
    query_spec: QuerySpec
    user_profile: UserProfile
    
    # Intermediate states
    candidates: List[Candidate]
    extracted: List[ExtractedEvent]
    
    # Output
    top10: List[Dict[str, Any]]
    
    # Control flow
    decision: Decision
    cycle_count: int
    total_cost: float
    
    # Tracking
    errors: List[str]
    logs: List[str]

# Agent node functions using ACTUAL v0.2.0 agents

def profile_planner_node(state: WorkflowState) -> WorkflowState:
    """The Editor agent node - using real EditorAgent."""
    state["logs"].append("The Editor: Building search profile from test data")
    
    # Initialize the real agent
    agent = EditorAgent()
    
    # Build profile from test CSV if not exists
    if not state.get("user_profile") or len(state["user_profile"]) == 0:
        # Build profile from actual test data
        profile = agent.build_user_profile()
        
        # Convert sets to lists for JSON serialization
        state["user_profile"] = {
            "allowlist_domains": list(profile["allowlist_domains"]),
            "keywords": profile["keywords"],
            "prior_feedback": profile["prior_feedback"],
            "interest_areas": profile["interest_areas"],
            "credentials": profile["credentials"],
            "location_preference": profile["location_preference"]
        }
        
        state["logs"].append(f"The Editor: Built profile with {len(profile['allowlist_domains'])} domains and {len(profile['keywords'])} keywords")
    
    # If this is a revision cycle, update strategy
    if state.get("decision", {}).get("action") == "revise":
        state["logs"].append(f"The Editor: Revising based on: {state['decision']['notes']}")
        
        # Expand search if needed
        if "expand" in state["decision"]["notes"].lower():
            # Add more domains
            current_domains = state["user_profile"]["allowlist_domains"]
            if len(current_domains) < 20:
                expanded_domains = list(agent.extract_domains_from_events())
                state["user_profile"]["allowlist_domains"] = expanded_domains[:20]
                state["logs"].append(f"The Editor: Expanded to {len(state['user_profile']['allowlist_domains'])} domains")
    
    # Plan search strategy based on query
    if state.get("query_spec"):
        strategy = agent.plan_search_strategy(state["user_profile"], state["query_spec"]["text"])
        state["logs"].append(f"The Editor: Search strategy uses {len(strategy['search_keywords'])} keywords")
    
    return state

def researcher_node(state: WorkflowState) -> WorkflowState:
    """The Researcher node - using real ResearcherAgent with v0.2.0 improvements."""
    state["logs"].append("The Researcher: Searching for events with Tavily API")
    
    # Initialize the researcher agent (multi-search, Facebook exclusion)
    agent = ResearcherAgent(use_cache=True)  # Use cache in real workflow
    
    # Get search parameters from state
    query_spec = state.get("query_spec", {})
    user_profile = state.get("user_profile", {})
    
    # Execute real Tavily search with v0.2.0 improvements
    try:
        candidates = agent.search_events(
            query=query_spec.get("text", "events in NYC"),
            keywords=user_profile.get("keywords", []),
            domains=user_profile.get("allowlist_domains", []),
            location=query_spec.get("city", "NYC"),
            date_from=query_spec.get("date_from"),
            date_to=query_spec.get("date_to"),
            max_results=20  # v0.3.0: Get 15-20 candidates
        )
        
        # Note: Date filtering is now handled by LLM in Fact-Checker, not here
        
        # Re-rank by relevance
        if candidates:
            candidates = agent.re_rank_by_relevance(
                candidates,
                user_profile.get("interest_areas", []),
                user_profile.get("keywords", [])
            )
        
        state["candidates"] = candidates
        state["logs"].append(f"The Researcher: Found {len(candidates)} candidates from Tavily")
        
        # Track cost (2 searches with multi-search)
        state["total_cost"] = state.get("total_cost", 0) + 0.02
        
    except Exception as e:
        state["logs"].append(f"The Researcher: Error during search - {str(e)}")
        state["errors"].append(f"Researcher error: {str(e)}")
        state["candidates"] = []
    
    return state

def fact_checker_node(state: WorkflowState) -> WorkflowState:
    """The Fact-Checker node - using real FactCheckerAgent with LLM deduplication."""
    num_candidates = len(state['candidates'])
    state["logs"].append(f"The Fact-Checker: Processing {num_candidates} candidates")
    
    if num_candidates == 0:
        state["extracted"] = []
        return state
    
    # Initialize the real Fact-Checker agent
    agent = FactCheckerAgent(use_cache=True)
    
    # v0.3.0: Extract more candidates for better coverage
    max_extractions = min(20, num_candidates)  # Increased from 3 to 20
    
    try:
        # Use the v0.2.0 extract_from_candidates with LLM deduplication
        extracted_events = agent.extract_from_candidates(
            state["candidates"][:max_extractions],
            max_extractions=max_extractions,
            use_llm=True  # Use LLM for deduplication and extraction
        )
        
        state["extracted"] = extracted_events
        state["total_cost"] = state.get("total_cost", 0) + (max_extractions * 0.01)  # Extraction cost
        
        # Add LLM cost for deduplication (approximately)
        if extracted_events:
            state["total_cost"] = state.get("total_cost", 0) + 0.001  # Small LLM cost
        
        # Log statistics
        basic_info_count = sum(1 for e in extracted_events if e.get("has_basic_info", False))
        past_events = sum(1 for e in extracted_events if e.get("is_past_event", False))
        
        state["logs"].append(f"The Fact-Checker: Extracted {len(extracted_events)} unique events")
        state["logs"].append(f"The Fact-Checker: {basic_info_count} have basic info, {past_events} are past events")
        
    except Exception as e:
        state["logs"].append(f"The Fact-Checker: Error - {str(e)}")
        state["errors"].append(f"Fact-Checker error: {str(e)}")
        state["extracted"] = []
    
    return state

def publisher_gate_node(state: WorkflowState) -> WorkflowState:
    """The Publisher/Gate node - using real PublisherAgent with v0.2.0 improvements."""
    num_events = len(state['extracted'])
    state["logs"].append(f"The Publisher: Scoring {num_events} events")
    
    # Increment cycle count before decision
    state["cycle_count"] = state.get("cycle_count", 0) + 1
    
    if num_events == 0:
        state["top10"] = []
        state["decision"] = {
            "action": "accept",  # Accept empty results after trying
            "notes": "No events to score"
        }
        return state
    
    # Initialize the real Publisher agent
    agent = PublisherAgent()
    
    try:
        # Use the v0.2.0 score_and_rank with better event presentation
        result = agent.score_and_rank(
            events=state["extracted"],
            user_profile=state["user_profile"],
            cycle_count=state.get("cycle_count", 0)
        )
        
        state["top10"] = result["top10"]
        state["decision"] = result["decision"]
        state["total_cost"] = state.get("total_cost", 0) + result.get("cost", 0)
        
        # Log statistics
        stats = result.get("stats", {})
        state["logs"].append(f"The Publisher: Scored {stats.get('scored_events', 0)} events")
        state["logs"].append(f"The Publisher: {stats.get('viable_events', 0)} viable events (score >= 0.3)")
        state["logs"].append(f"The Publisher: Decision={result['decision']['action']} - {result['decision']['notes']}")
        
    except Exception as e:
        state["logs"].append(f"The Publisher: Error - {str(e)}")
        state["errors"].append(f"Publisher error: {str(e)}")
        # Fallback decision
        state["top10"] = []
        state["decision"] = {
            "action": "accept",
            "notes": f"Error during scoring: {str(e)}"
        }
    
    return state

# Routing function for cycle
def should_continue(state: WorkflowState) -> str:
    """Determine whether to continue the cycle or finish."""
    if state["decision"]["action"] == "revise" and state.get("cycle_count", 0) < 2:
        return "profile_planner"  # Loop back
    else:
        return "end"  # Finish

# Build the workflow graph
def create_workflow() -> StateGraph:
    """Create the LangGraph workflow with actual v0.2.0 agents."""
    
    # Initialize the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes with actual agent implementations
    workflow.add_node("profile_planner", profile_planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("publisher_gate", publisher_gate_node)
    
    # Add edges for linear flow
    workflow.add_edge("profile_planner", "researcher")
    workflow.add_edge("researcher", "fact_checker")
    workflow.add_edge("fact_checker", "publisher_gate")
    
    # Add conditional edge for cycle
    workflow.add_conditional_edges(
        "publisher_gate",
        should_continue,
        {
            "profile_planner": "profile_planner",  # Loop back
            "end": END  # Finish
        }
    )
    
    # Set entry point
    workflow.set_entry_point("profile_planner")
    
    return workflow.compile()

# Helper function to run the workflow
def run_workflow(query: str, city: str = "NYC", days_ahead: int = 14) -> Dict[str, Any]:
    """Run the complete workflow with a query."""
    
    # Prepare initial state
    initial_state = {
        "query_spec": {
            "text": query,
            "city": city,
            "date_from": datetime.now(),
            "date_to": datetime.now() + timedelta(days=days_ahead),
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
    
    # Create and run workflow
    app = create_workflow()
    
    # Set recursion limit to prevent infinite loops
    config = {"recursion_limit": 3}
    result = app.invoke(initial_state, config=config)
    
    return result

# Test function
def test_workflow():
    """Test the workflow with a sample query."""
    print("Testing LangGraph Workflow with v0.2.0 Agents")
    print("=" * 50)
    
    # Run with test query
    result = run_workflow(
        query="Find protests and cultural events in NYC",
        city="NYC",
        days_ahead=14
    )
    
    # Display results
    print(f"\nQuery: {result['query_spec']['text']}")
    print(f"City: {result['query_spec']['city']}")
    print(f"Date Range: {result['query_spec']['date_from'].date()} to {result['query_spec']['date_to'].date()}")
    
    print(f"\nWorkflow executed with {result['cycle_count']} cycles")
    print(f"Total cost: ${result['total_cost']:.4f}")
    
    print(f"\nTop {len(result['top10'])} Recommendations:")
    for i, event in enumerate(result['top10'], 1):
        print(f"\n{i}. {event.get('title', 'Unknown')}")
        print(f"   Score: {event.get('recommendation', 0):.2f}")
        print(f"   Location: {event.get('location', 'Unknown')}")
        print(f"   Access: {event.get('access_req', 'Unknown')}")
        print(f"   Rationale: {event.get('rationale', '')}")
    
    print("\nWorkflow Logs:")
    for log in result['logs']:
        print(f"  • {log}")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  ⚠️ {error}")

if __name__ == "__main__":
    test_workflow()