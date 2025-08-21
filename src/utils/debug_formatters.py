"""Debug formatters for agent outputs to create human-readable displays."""

from typing import Dict, List, Any
from collections import Counter
from datetime import datetime


def format_editor_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format Editor agent output for debug display.
    
    Args:
        state: Workflow state after Editor processing
        
    Returns:
        Formatted data for UI display
    """
    profile = state.get("profile", {})
    metrics = state.get("editor_metrics", {})
    
    return {
        "summary": "Profile Created",
        "profile": {
            "location": profile.get("location", "Not specified"),
            "timeframe": profile.get("time_frame", "Not specified"),
            "interests": profile.get("interests", []),
            "iteration": profile.get("iteration", 1)
        },
        "guidance": profile.get("researcher_guidance", "No guidance provided"),
        "metrics": {
            "cost": f"${metrics.get('cost', 0):.4f}",
            "time": f"{metrics.get('elapsed_time', 0):.1f}s",
            "tokens": metrics.get("total_tokens", 0)
        },
        "raw_data": {
            "profile": profile,
            "metrics": metrics
        }
    }


def format_researcher_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format Researcher agent output for debug display.
    
    Args:
        state: Workflow state after Researcher processing
        
    Returns:
        Formatted data for UI display
    """
    leads = state.get("leads", [])
    metrics = state.get("researcher_metrics", {})
    
    # Analyze lead types
    lead_types = Counter(lead.get("type", "unknown") for lead in leads)
    
    # Preview first 5 leads
    preview_leads = []
    for i, lead in enumerate(leads[:5], 1):
        preview_leads.append({
            "number": i,
            "description": lead.get("description", "No description"),
            "type": lead.get("type", "unknown"),
            "keywords": lead.get("keywords", []),
            "search_query": lead.get("search_query", "No query")
        })
    
    return {
        "summary": f"Generated {len(leads)} Event Leads",
        "total_leads": len(leads),
        "lead_types": dict(lead_types),
        "preview": preview_leads,
        "show_all": len(leads) > 5,
        "metrics": {
            "cost": f"${metrics.get('cost', 0):.4f}",
            "time": f"{metrics.get('elapsed_time', 0):.1f}s",
            "tokens": metrics.get("total_tokens", 0)
        },
        "raw_data": {
            "leads": leads,
            "metrics": metrics
        }
    }


def format_fact_checker_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format Fact-Checker agent output for debug display.
    
    Args:
        state: Workflow state after Fact-Checker processing
        
    Returns:
        Formatted data for UI display
    """
    evidence = state.get("evidence", [])
    metrics = state.get("fact_checker_metrics", {})
    
    # Analyze search results
    search_summary = []
    total_results = 0
    cache_hits = 0
    
    for item in evidence:
        lead = item.get("lead", {})
        results = item.get("results", [])
        
        search_summary.append({
            "description": lead.get("description", "Unknown lead"),
            "results_found": len(results),
            "status": "✓ Found" if results else "✗ No results",
            "top_sources": [r.get("url", "")[:50] + "..." for r in results[:2]],
            "preview_results": results[:2]  # First 2 results for expansion
        })
        
        total_results += len(results)
    
    return {
        "summary": f"Searched for {len(evidence)} Event Leads",
        "total_searches": len(evidence),
        "total_results": total_results,
        "searches_with_results": sum(1 for s in search_summary if s["results_found"] > 0),
        "search_details": search_summary,
        "metrics": {
            "cost": f"${metrics.get('cost', 0):.4f}",
            "time": f"{metrics.get('elapsed_time', 0):.1f}s",
            "searches": metrics.get("total_searches", len(evidence)),
            "cache_hits": f"{metrics.get('cache_hits', 0)}/{len(evidence)}"
        },
        "raw_data": {
            "evidence": evidence,
            "metrics": metrics
        }
    }


def format_publisher_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format Publisher agent output for debug display.
    
    Args:
        state: Workflow state after Publisher processing
        
    Returns:
        Formatted data for UI display
    """
    events = state.get("events", [])
    gate_decision = state.get("gate_decision", "UNKNOWN")
    feedback = state.get("feedback")
    metrics = state.get("publisher_metrics", {})
    
    # Format events preview
    events_preview = []
    for i, event in enumerate(events[:5], 1):
        events_preview.append({
            "number": i,
            "title": event.get("title", "Untitled"),
            "date": event.get("date", "No date"),
            "time": event.get("time", "No time specified"),
            "location": event.get("location", "No location"),
            "score": event.get("score", 0),
            "has_url": bool(event.get("url")),
            "has_description": bool(event.get("description"))
        })
    
    # Count events with complete info
    events_with_time = sum(1 for e in events if e.get("time"))
    events_with_desc = sum(1 for e in events if e.get("description"))
    events_with_url = sum(1 for e in events if e.get("url"))
    
    result = {
        "summary": f"Extracted Events → Gate Decision: {gate_decision}",
        "gate_decision": gate_decision,
        "total_events": len(events),
        "events_preview": events_preview,
        "show_all_events": len(events) > 5,
        "quality_metrics": {
            "with_time": f"{events_with_time}/{len(events)}",
            "with_description": f"{events_with_desc}/{len(events)}",
            "with_url": f"{events_with_url}/{len(events)}"
        },
        "metrics": {
            "cost": f"${metrics.get('cost', 0):.4f}",
            "time": f"{metrics.get('elapsed_time', 0):.1f}s",
            "tokens": metrics.get("total_tokens", 0)
        },
        "raw_data": {
            "events": events,
            "metrics": metrics
        }
    }
    
    if gate_decision == "RETRY" and feedback:
        result["feedback"] = feedback
        result["retry_reason"] = feedback
    
    return result


def format_error_output(agent_name: str, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Format error output for debug display.
    
    Args:
        agent_name: Name of the agent that failed
        error: The exception that occurred
        context: Additional context about the error
        
    Returns:
        Formatted error data for UI display
    """
    return {
        "summary": f"❌ Agent Error: {agent_name}",
        "agent": agent_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat(),
        "debug_info": context or {},
        "raw_error": {
            "type": type(error).__name__,
            "message": str(error),
            "context": context
        }
    }