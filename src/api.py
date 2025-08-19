"""FastAPI endpoints for LocAIted."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent
from cache_manager import CacheManager
from database import SessionLocal, Event, User, Recommendation

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

if __name__ == "__main__":
    import uvicorn
    print("Starting LocAIted API server...")
    print("API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)