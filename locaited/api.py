"""FastAPI endpoints for LocAIted."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import json
import asyncio
from pathlib import Path

# No longer need to modify sys.path with proper package installation

from locaited.agents.editor import EditorAgent
from locaited.agents.researcher import ResearcherAgent
from locaited.agents.fact_checker import FactCheckerAgent
from locaited.agents.publisher import PublisherAgent
from locaited.cache_manager import CacheManager
from locaited.database import SessionLocal, Event, User, Recommendation
from locaited.utils.debug_formatters import (
    format_editor_output,
    format_researcher_output,
    format_fact_checker_output,
    format_publisher_output,
    format_error_output
)

app = FastAPI(title="LocAIted API", version="1.0.0")

# Enable CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache manager instance
cache = CacheManager()

# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    location: str = "NYC"
    days_ahead: int = 14
    use_cache: bool = True

class ExtendedSearchRequest(BaseModel):
    """Extended request for single-flow UI with profile + query."""
    query: str
    location: str = "NYC"
    custom_location: Optional[str] = None
    interest_areas: List[str] = []
    csv_file: Optional[str] = None  # Base64 encoded CSV
    days_ahead: int = 7  # 7, 14, or 30
    use_cache: bool = True

class ProfileRequest(BaseModel):
    csv_path: Optional[str] = None
    interests: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    credentials: Optional[List[str]] = None

class EventResponse(BaseModel):
    title: str
    location: str
    time: Optional[str]
    url: str
    access_req: str
    summary: str
    score: float
    rationale: Optional[str] = None

class ProfileResponse(BaseModel):
    domains: List[str]
    keywords: List[str]
    interest_areas: List[str]
    credentials: List[str]
    location_preference: str

class WorkflowResponse(BaseModel):
    events: List[EventResponse]
    total_cost: float
    cache_hits: int
    status: str
    message: str

# Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "LocAIted API"}

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return cache.get_cache_stats()

@app.post("/cache/clear")
async def clear_expired_cache():
    """Clear expired cache entries."""
    removed = cache.clear_expired_cache()
    return {"removed_entries": removed}

@app.post("/profile/build", response_model=ProfileResponse)
async def build_profile(request: ProfileRequest):
    """Build user profile from CSV or manual input."""
    try:
        agent = EditorAgent()
        
        if request.csv_path:
            # Build from CSV (for testing)
            profile = agent.build_user_profile()
        else:
            # Build from provided data
            profile = {
                "allowlist_domains": [],
                "keywords": request.keywords or [],
                "interest_areas": request.interests or [],
                "credentials": request.credentials or ["none"],
                "location_preference": "NYC",
                "prior_feedback": []
            }
            
            # Extract domains from interests
            if request.interests:
                domains = agent.extract_domains_from_events()
                profile["allowlist_domains"] = list(domains)[:20]
        
        return ProfileResponse(
            domains=profile["allowlist_domains"],
            keywords=profile["keywords"],
            interest_areas=profile["interest_areas"],
            credentials=profile["credentials"],
            location_preference=profile["location_preference"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[EventResponse])
async def search_events(request: SearchRequest):
    """Search for events using Tavily API."""
    try:
        # Build default profile
        editor = EditorAgent()
        profile = editor.build_user_profile()
        
        # Search with researcher
        researcher = ResearcherAgent(use_cache=request.use_cache)
        
        date_from = datetime.now()
        date_to = date_from + timedelta(days=request.days_ahead)
        
        candidates = researcher.search_events(
            query=request.query,
            keywords=profile["keywords"][:10],
            domains=profile["allowlist_domains"][:10],
            location=request.location,
            date_from=date_from,
            date_to=date_to,
            max_results=10
        )
        
        # Re-rank
        if candidates:
            candidates = researcher.re_rank_by_relevance(
                candidates,
                profile["interest_areas"],
                profile["keywords"]
            )
        
        # Convert to response format
        events = []
        for c in candidates[:10]:
            events.append(EventResponse(
                title=c.get("title", "Unknown"),
                location=request.location,
                time=c.get("published_date"),
                url=c["url"],
                access_req="unknown",
                summary=c["snippet"],
                score=c.get("relevance_score", c["score"])
            ))
        
        return events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/run", response_model=WorkflowResponse)
async def run_workflow(request: SearchRequest):
    """Run complete workflow: Profile -> Search -> Extract -> Recommend."""
    try:
        cache_hits = 0
        total_cost = 0.0
        
        # 1. Build profile
        editor = EditorAgent()
        profile = editor.build_user_profile()
        
        # 2. Search
        researcher = ResearcherAgent(use_cache=request.use_cache)
        
        # Check if search is cached
        if request.use_cache:
            cached = cache.get_search_cache(
                query=request.query,
                keywords=profile["keywords"][:10],
                domains=profile["allowlist_domains"][:10],
                location=request.location
            )
            if cached:
                cache_hits += 1
        
        date_from = datetime.now()
        date_to = date_from + timedelta(days=request.days_ahead)
        
        candidates = researcher.search_events(
            query=request.query,
            keywords=profile["keywords"][:10],
            domains=profile["allowlist_domains"][:10],
            location=request.location,
            date_from=date_from,
            date_to=date_to,
            max_results=10
        )
        
        if not candidates:
            return WorkflowResponse(
                events=[],
                total_cost=0.01,
                cache_hits=cache_hits,
                status="no_results",
                message="No events found matching your query"
            )
        
        # Re-rank
        candidates = researcher.re_rank_by_relevance(
            candidates,
            profile["interest_areas"],
            profile["keywords"]
        )
        
        total_cost += 0.01  # Search cost
        
        # 3. Extract (top 2 only to save credits)
        fact_checker = FactCheckerAgent(use_cache=request.use_cache)
        extracted = fact_checker.extract_from_candidates(
            candidates[:2],
            max_extractions=2
        )
        
        # Count cache hits for extraction
        if request.use_cache:
            for c in candidates[:2]:
                if cache.get_extract_cache(c["url"]):
                    cache_hits += 1
        
        total_cost += len(extracted) * 0.01  # Extract cost
        
        if not extracted:
            # Return search results without extraction
            events = []
            for c in candidates[:5]:
                events.append(EventResponse(
                    title=c.get("title", "Unknown"),
                    location=request.location,
                    time=None,
                    url=c["url"],
                    access_req="unknown",
                    summary=c["snippet"],
                    score=c.get("relevance_score", c["score"])
                ))
            
            return WorkflowResponse(
                events=events,
                total_cost=total_cost,
                cache_hits=cache_hits,
                status="extraction_failed",
                message="Could not extract detailed information"
            )
        
        # 4. Recommend
        publisher = PublisherAgent()
        
        # Check LLM cache
        if request.use_cache:
            cached_llm = cache.get_llm_cache(extracted, profile)
            if cached_llm:
                cache_hits += 1
                result = cached_llm
            else:
                result = publisher.score_and_rank(extracted, profile, cycle_count=0)
                cache.save_llm_cache(extracted, profile, result)
        else:
            result = publisher.score_and_rank(extracted, profile, cycle_count=0)
        
        total_cost += result.get("cost", 0)
        
        # Convert to response
        events = []
        for event in result["top10"]:
            events.append(EventResponse(
                title=event.get("title", "Unknown"),
                location=event.get("location", request.location),
                time=str(event.get("time")) if event.get("time") else None,
                url=event.get("url", ""),
                access_req=event.get("access_req", "unknown"),
                summary=event.get("summary", ""),
                score=event.get("recommendation", 0),
                rationale=event.get("rationale", "")
            ))
        
        return WorkflowResponse(
            events=events,
            total_cost=total_cost,
            cache_hits=cache_hits,
            status="success",
            message=f"Found {len(events)} recommended events"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/discover", response_model=WorkflowResponse)
async def discover_events(request: ExtendedSearchRequest):
    """Single-flow endpoint for UI: accepts profile + query, runs v0.4.0 workflow."""
    try:
        # Import workflow
        from locaited.agents.workflow import Workflow
        
        # Use custom location if provided
        location = request.custom_location if request.custom_location else request.location
        
        # Parse CSV if provided (optional for MVP)
        previous_events = []
        if request.csv_file:
            # Basic CSV parsing would go here
            # For MVP, we'll skip complex parsing
            pass
        
        # Build user input for workflow v0.4.0
        user_input = {
            "location": location,
            "time_frame": f"next {request.days_ahead} days",
            "interests": request.interest_areas,
            "query": request.query
        }
        
        # Initialize and run workflow
        workflow = Workflow(use_cache=request.use_cache)
        result = workflow.run_workflow(user_input)
        
        # Format events for response
        events = []
        for event in result.get("events", []):
            events.append(EventResponse(
                title=event.get("title", "Unknown"),
                location=event.get("location", location),
                time=event.get("time"),
                url=event.get("url", ""),
                access_req=event.get("access_req", "unknown"),
                summary=event.get("description", ""),
                score=event.get("score", 0),
                rationale=event.get("rationale", "")
            ))
        
        # Get metrics from workflow
        metrics = result.get("workflow_metrics", {})
        
        # Handle error cases gracefully
        status = result.get("gate_decision", "success")
        if status == "ERROR" and not events:
            # Return a meaningful error response but still valid
            return WorkflowResponse(
                events=[],
                total_cost=metrics.get("total_cost", 0),
                cache_hits=metrics.get("cache_hits", 0),
                status="error",
                message="Workflow encountered an error. Please try again with cache enabled."
            )
        
        return WorkflowResponse(
            events=events,
            total_cost=metrics.get("total_cost", 0),
            cache_hits=metrics.get("cache_hits", 0),
            status=status if status != "ERROR" else "success",
            message=result.get("feedback", f"Found {len(events)} events")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/discover-test", response_model=WorkflowResponse)
async def discover_events_test(request: ExtendedSearchRequest):
    """Test endpoint that returns mock data quickly for UI testing."""
    # Return mock data immediately to test UI
    mock_events = [
        EventResponse(
            title="Fashion Week Opening Gala",
            location="Bryant Park, NYC",
            time="2025-08-25 18:00",
            url="https://example.com/fashion-week",
            access_req="public_only",
            summary="Annual fashion week opening ceremony featuring emerging designers",
            score=95,
            rationale="Highly relevant fashion event in NYC"
        ),
        EventResponse(
            title="Tech & Fashion Symposium",
            location="Museum of Modern Art, NYC",
            time="2025-08-26 14:00",
            url="https://example.com/tech-fashion",
            access_req="public_only",
            summary="Exploring the intersection of technology and fashion design",
            score=88,
            rationale="Combines both fashion and technology interests"
        ),
        EventResponse(
            title="Sustainable Fashion Showcase",
            location="Chelsea Market, NYC",
            time="2025-08-27 10:00",
            url="https://example.com/sustainable",
            access_req="public_only",
            summary="Exhibition of eco-friendly fashion brands and innovations",
            score=82,
            rationale="Important fashion industry trend"
        )
    ]
    
    return WorkflowResponse(
        events=mock_events,
        total_cost=0.05,
        cache_hits=3,
        status="success",
        message=f"Test data: Found {len(mock_events)} mock events"
    )

@app.get("/events/recent", response_model=List[EventResponse])
async def get_recent_events(limit: int = 10):
    """Get recently processed events from database."""
    try:
        db = SessionLocal()
        try:
            events = db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
            
            response = []
            for event in events:
                response.append(EventResponse(
                    title=event.title,
                    location=event.location,
                    time=event.start_time.isoformat() if event.start_time else None,
                    url=event.source_url,
                    access_req=event.access_requirements or "unknown",
                    summary=event.description or "",
                    score=0.5  # Default score
                ))
            
            return response
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Global state for debug sessions
debug_sessions = {}


@app.post("/workflow/discover-debug")
async def discover_events_debug(request: ExtendedSearchRequest):
    """Debug endpoint for step-by-step workflow execution with SSE streaming."""
    
    # Create unique session ID
    session_id = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Initialize session state
    debug_sessions[session_id] = {
        "status": "starting",
        "current_agent": None,
        "continue_event": asyncio.Event(),
        "stop_requested": False
    }
    
    async def event_stream():
        try:
            # Import workflow
            from locaited.agents.workflow import Workflow
            
            # Use custom location if provided
            location = request.custom_location if request.custom_location else request.location
            
            # Build user input for workflow
            user_input = {
                "location": location,
                "time_frame": f"next {request.days_ahead} days",
                "interests": request.interest_areas,
                "query": request.query
            }
            
            # Send initial event
            yield f"data: {json.dumps({'event': 'session_start', 'session_id': session_id, 'user_input': user_input})}\n\n"
            
            # Initialize workflow components with cache preference
            use_cache = request.use_cache if hasattr(request, 'use_cache') else True
            editor = EditorAgent()
            researcher = ResearcherAgent(use_cache=use_cache)
            fact_checker = FactCheckerAgent(use_cache=use_cache)
            publisher = PublisherAgent(use_cache=use_cache)
            
            # Initialize state
            state = {"user_input": f"{user_input['query']} in {user_input['location']} for {user_input['time_frame']}"}
            
            # Editor Agent
            debug_sessions[session_id]["current_agent"] = "editor"
            yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'editor'})}\n\n"
            
            try:
                start_time = datetime.now()
                state = editor.process(state)
                end_time = datetime.now()
                
                # Add timing metrics
                state["editor_metrics"] = state.get("editor_metrics", {})
                state["editor_metrics"]["elapsed_time"] = (end_time - start_time).total_seconds()
                
                # Format and send editor results
                formatted_output = format_editor_output(state)
                yield f"data: {json.dumps({'event': 'agent_complete', 'agent': 'editor', 'data': formatted_output})}\n\n"
                
                # Wait for continue signal
                yield f"data: {json.dumps({'event': 'waiting_continue', 'agent': 'editor'})}\n\n"
                await debug_sessions[session_id]["continue_event"].wait()
                debug_sessions[session_id]["continue_event"].clear()
                
                if debug_sessions[session_id]["stop_requested"]:
                    yield f"data: {json.dumps({'event': 'debug_stopped', 'agent': 'editor'})}\n\n"
                    return
                    
            except Exception as e:
                error_output = format_error_output("editor", e)
                yield f"data: {json.dumps({'event': 'agent_error', 'agent': 'editor', 'data': error_output})}\n\n"
                return
            
            # Researcher Agent
            debug_sessions[session_id]["current_agent"] = "researcher"
            yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'researcher'})}\n\n"
            
            try:
                start_time = datetime.now()
                state = researcher.process(state)
                end_time = datetime.now()
                
                # Add timing metrics
                state["researcher_metrics"] = state.get("researcher_metrics", {})
                state["researcher_metrics"]["elapsed_time"] = (end_time - start_time).total_seconds()
                
                # Format and send researcher results
                formatted_output = format_researcher_output(state)
                yield f"data: {json.dumps({'event': 'agent_complete', 'agent': 'researcher', 'data': formatted_output})}\n\n"
                
                # Wait for continue signal
                yield f"data: {json.dumps({'event': 'waiting_continue', 'agent': 'researcher'})}\n\n"
                await debug_sessions[session_id]["continue_event"].wait()
                debug_sessions[session_id]["continue_event"].clear()
                
                if debug_sessions[session_id]["stop_requested"]:
                    yield f"data: {json.dumps({'event': 'debug_stopped', 'agent': 'researcher'})}\n\n"
                    return
                    
            except Exception as e:
                error_output = format_error_output("researcher", e)
                yield f"data: {json.dumps({'event': 'agent_error', 'agent': 'researcher', 'data': error_output})}\n\n"
                return
            
            # Fact-Checker Agent
            debug_sessions[session_id]["current_agent"] = "fact_checker"
            yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'fact_checker'})}\n\n"
            
            try:
                start_time = datetime.now()
                state = fact_checker.process(state)
                end_time = datetime.now()
                
                # Add timing metrics
                state["fact_checker_metrics"] = state.get("fact_checker_metrics", {})
                state["fact_checker_metrics"]["elapsed_time"] = (end_time - start_time).total_seconds()
                
                # Format and send fact-checker results
                formatted_output = format_fact_checker_output(state)
                yield f"data: {json.dumps({'event': 'agent_complete', 'agent': 'fact_checker', 'data': formatted_output})}\n\n"
                
                # Wait for continue signal
                yield f"data: {json.dumps({'event': 'waiting_continue', 'agent': 'fact_checker'})}\n\n"
                await debug_sessions[session_id]["continue_event"].wait()
                debug_sessions[session_id]["continue_event"].clear()
                
                if debug_sessions[session_id]["stop_requested"]:
                    yield f"data: {json.dumps({'event': 'debug_stopped', 'agent': 'fact_checker'})}\n\n"
                    return
                    
            except Exception as e:
                error_output = format_error_output("fact_checker", e)
                yield f"data: {json.dumps({'event': 'agent_error', 'agent': 'fact_checker', 'data': error_output})}\n\n"
                return
            
            # Publisher Agent
            debug_sessions[session_id]["current_agent"] = "publisher"
            yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'publisher'})}\n\n"
            
            try:
                start_time = datetime.now()
                state = publisher.process(state)
                end_time = datetime.now()
                
                # Add timing metrics
                state["publisher_metrics"] = state.get("publisher_metrics", {})
                state["publisher_metrics"]["elapsed_time"] = (end_time - start_time).total_seconds()
                
                # Format and send publisher results
                formatted_output = format_publisher_output(state)
                yield f"data: {json.dumps({'event': 'agent_complete', 'agent': 'publisher', 'data': formatted_output})}\n\n"
                
                # Final completion
                yield f"data: {json.dumps({'event': 'workflow_complete', 'final_state': state})}\n\n"
                
            except Exception as e:
                error_output = format_error_output("publisher", e)
                yield f"data: {json.dumps({'event': 'agent_error', 'agent': 'publisher', 'data': error_output})}\n\n"
                return
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'workflow_error', 'error': str(e)})}\n\n"
        finally:
            # Clean up session
            if session_id in debug_sessions:
                del debug_sessions[session_id]
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.post("/workflow/debug-continue/{session_id}")
async def debug_continue(session_id: str):
    """Signal debug session to continue to next agent."""
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    debug_sessions[session_id]["continue_event"].set()
    return {"status": "continue_signal_sent"}


@app.post("/workflow/debug-stop/{session_id}")
async def debug_stop(session_id: str):
    """Signal debug session to stop."""
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    debug_sessions[session_id]["stop_requested"] = True
    debug_sessions[session_id]["continue_event"].set()  # Unblock if waiting
    return {"status": "stop_signal_sent"}


if __name__ == "__main__":
    import uvicorn
    print("Starting LocAIted API server...")
    print("API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)