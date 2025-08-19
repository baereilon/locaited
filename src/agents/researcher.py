"""The Researcher for LocAIted - Multi-search with domain filtering."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tavily import TavilyClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TAVILY_API_KEY, TAVILY_SEARCH_DEPTH, TAVILY_MAX_RESULTS
from cache_manager import CacheManager

class ResearcherAgent:
    """The Researcher: Like an investigative journalist, finds relevant events from multiple angles."""
    
    def __init__(self, api_key: str = TAVILY_API_KEY, use_cache: bool = True):
        """Initialize Tavily client."""
        self.client = TavilyClient(api_key=api_key)
        self.last_search_cost = 0.0
        self.use_cache = use_cache
        self.cache = CacheManager() if use_cache else None
        
        # Facebook exclusion list
        self.excluded_domains = [
            "facebook.com",
            "fb.com",
            "m.facebook.com",
            "web.facebook.com"
        ]
        
        # Strong sources for different event types
        self.event_type_domains = {
            "protests": ["twitter.com", "x.com", "indymedia.org", "reddit.com"],
            "cultural": ["timeout.com", "eventbrite.com", "nyc.gov", "nycgo.com"],
            "political": ["nyc.gov", "council.nyc.gov", "twitter.com", "ny1.com"],
            "scheduled": ["eventbrite.com", "meetup.com", "nyc.gov", "timeout.com"]
        }
        
    def build_search_queries(self, 
                           base_query: str,
                           keywords: List[str],
                           location: str = "NYC",
                           event_type: str = None) -> List[str]:
        """Build multiple search queries for different angles."""
        
        queries = []
        
        # Query 1: General event search with date context
        general_parts = [base_query, location, "events", "upcoming 2025"]
        queries.append(" ".join(general_parts))
        
        # Query 2: Targeted search with site operators
        if event_type and event_type in self.event_type_domains:
            domains = self.event_type_domains[event_type]
            site_operators = " OR ".join([f"site:{d}" for d in domains[:3]])
            targeted = f"({site_operators}) {base_query} {location}"
            queries.append(targeted)
        elif keywords:
            # Use keywords for targeted search
            keyword_focus = " OR ".join(keywords[:3])
            queries.append(f"({keyword_focus}) events {location} 2025")
        
        return queries
    
    def search_events_multi(self,
                          query: str,
                          keywords: List[str] = None,
                          domains: List[str] = None,
                          location: str = "NYC",
                          date_from: datetime = None,
                          date_to: datetime = None,
                          max_results: int = 20,  # Increased for v0.3.0
                          num_searches: int = 2) -> List[Dict[str, Any]]:
        """
        Perform multiple searches with different strategies.
        
        Args:
            query: Main search query
            keywords: Additional keywords to include
            domains: List of preferred domains
            location: Location filter
            date_from: Start date for events
            date_to: End date for events
            max_results: Maximum results per search
            num_searches: Number of different searches to perform (max 2)
            
        Returns:
            Combined and deduplicated list of candidates
        """
        
        all_candidates = []
        seen_urls = set()
        
        # Determine event type from query
        event_type = None
        query_lower = query.lower()
        if "protest" in query_lower or "march" in query_lower:
            event_type = "protests"
        elif "cultural" in query_lower or "festival" in query_lower:
            event_type = "cultural"
        elif "political" in query_lower or "government" in query_lower:
            event_type = "political"
        else:
            event_type = "scheduled"
        
        # Build search queries
        search_queries = self.build_search_queries(query, keywords or [], location, event_type)
        
        # Perform searches
        for i, search_query in enumerate(search_queries[:num_searches]):
            print(f"\nSearch {i+1}/{num_searches}: {search_query[:100]}...")
            
            # Use different search depths for different queries
            search_depth = "advanced" if i == 0 and event_type == "scheduled" else TAVILY_SEARCH_DEPTH
            
            # For v0.3.0: Get more results per search to reach 15-20 total
            results_per_search = max(10, max_results // num_searches)
            candidates = self.search_single(
                query=search_query,
                domains=domains,
                location=location,
                max_results=results_per_search,
                search_depth=search_depth,
                date_from=date_from,
                date_to=date_to
            )
            
            # Deduplicate and add to results
            for candidate in candidates:
                url = candidate["url"]
                
                # Skip Facebook results
                if any(excluded in url.lower() for excluded in self.excluded_domains):
                    continue
                
                # Skip duplicates
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_candidates.append(candidate)
        
        print(f"\nTotal unique results from {num_searches} searches: {len(all_candidates)}")
        
        return all_candidates
    
    def search_single(self,
                     query: str,
                     domains: List[str] = None,
                     location: str = "NYC",
                     max_results: int = TAVILY_MAX_RESULTS,
                     search_depth: str = TAVILY_SEARCH_DEPTH,
                     date_from: datetime = None,
                     date_to: datetime = None) -> List[Dict[str, Any]]:
        """
        Perform a single search with Tavily API.
        
        Args:
            query: Search query
            domains: Optional domain filtering
            location: Location for search context
            max_results: Max results to return
            search_depth: "basic" or "advanced"
            date_from: Start date context
            date_to: End date context
            
        Returns:
            List of search candidates
        """
        
        # Add date context to query if provided
        if date_from and date_to:
            days_ahead = (date_to - date_from).days
            query += f" next {days_ahead} days"
        
        # Prepare search parameters
        search_params = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_raw_content": False,
            "include_images": False,
            "include_answer": True  # v0.3.0: Get AI-generated answer/overview
        }
        
        # Add domain filtering if provided (exclude Facebook)
        if domains and len(domains) > 0:
            # Filter out Facebook domains
            filtered_domains = [d for d in domains 
                              if not any(excluded in d.lower() 
                                       for excluded in self.excluded_domains)]
            if filtered_domains:
                search_params["include_domains"] = filtered_domains[:10]
        
        # Add exclusion for Facebook
        search_params["exclude_domains"] = self.excluded_domains
        
        # Check cache first
        if self.use_cache and self.cache:
            cache_key = f"{query}_{search_depth}"
            cached_results = self.cache.get_search_cache(
                query=cache_key,
                keywords=[],
                domains=domains or [],
                location=location  # Keep location in cache key
            )
            if cached_results:
                print(f"Using cached results for: {query[:50]}... (saved API credit)")
                return cached_results
        
        # Execute search
        try:
            response = self.client.search(**search_params)
            
            # v0.3.0: Capture the AI-generated answer/overview if available
            search_answer = response.get("answer", "")
            if search_answer:
                print(f"Tavily provided answer (length: {len(search_answer)} chars)")
            
            # Process results
            candidates = []
            for result in response.get("results", []):
                # Double-check Facebook exclusion
                url = result.get("url", "")
                if any(excluded in url.lower() for excluded in self.excluded_domains):
                    continue
                    
                candidate = {
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("content", "")[:500],
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date"),
                    "search_depth": search_depth,
                    "overview": search_answer  # v0.3.0: Add full overview from Tavily
                }
                candidates.append(candidate)
            
            # Sort by score
            candidates.sort(key=lambda x: x["score"], reverse=True)
            
            # Save to cache
            if self.use_cache and self.cache and candidates:
                self.cache.save_search_cache(
                    query=cache_key,
                    keywords=[],
                    domains=domains or [],
                    location=location,  # Keep location in cache
                    results=candidates
                )
            
            print(f"Found {len(candidates)} results (depth: {search_depth})")
            return candidates
            
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    def search_events(self,
                     query: str,
                     keywords: List[str] = None,
                     domains: List[str] = None,
                     location: str = "NYC",
                     date_from: datetime = None,
                     date_to: datetime = None,
                     max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Main search method - performs multi-search with deduplication.
        Backward compatible with existing code.
        
        Note: Date filtering is handled by LLM in Fact-Checker, not here.
        We pass date context to help Tavily find relevant results.
        """
        
        # Perform multi-search
        candidates = self.search_events_multi(
            query=query,
            keywords=keywords,
            domains=domains,
            location=location,
            date_from=date_from,
            date_to=date_to,
            max_results=max_results,
            num_searches=2  # Use 2 searches as per requirements
        )
        
        # Re-rank by relevance if we have keywords
        if candidates and keywords:
            candidates = self.re_rank_by_relevance(
                candidates, 
                self._extract_interests(keywords), 
                keywords
            )
        
        # Note: No date filtering here - let LLM handle it
        return candidates
    
    def _extract_interests(self, keywords: List[str]) -> List[str]:
        """Extract interest areas from keywords."""
        interest_keywords = {
            "protest": ["protest", "march", "rally", "demonstration"],
            "cultural": ["cultural", "festival", "art", "music", "theater"],
            "political": ["political", "government", "mayor", "council", "policy"]
        }
        
        interests = []
        for interest, terms in interest_keywords.items():
            if any(term in keyword.lower() for keyword in keywords for term in terms):
                interests.append(interest)
        
        return interests
    
    def filter_by_date(self, 
                      candidates: List[Dict[str, Any]], 
                      date_from: datetime,
                      date_to: datetime) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Date filtering now handled by LLM in Fact-Checker.
        Kept for backward compatibility only.
        """
        # Just return candidates as-is
        print("Note: Date filtering is now handled by LLM in Fact-Checker")
        return candidates
    
    def re_rank_by_relevance(self,
                            candidates: List[Dict[str, Any]],
                            interest_areas: List[str],
                            keywords: List[str]) -> List[Dict[str, Any]]:
        """Re-rank candidates based on user interests and keywords."""
        
        for candidate in candidates:
            relevance_score = candidate["score"]  # Start with Tavily score
            
            # Boost score for matching interests
            snippet_lower = candidate["snippet"].lower()
            title_lower = candidate["title"].lower()
            
            # Higher boost for title matches
            for interest in interest_areas:
                if interest.lower() in title_lower:
                    relevance_score += 0.15
                elif interest.lower() in snippet_lower:
                    relevance_score += 0.1
            
            # Boost score for matching keywords
            for keyword in keywords[:10]:  # Check top 10 keywords
                if keyword.lower() in title_lower:
                    relevance_score += 0.08
                elif keyword.lower() in snippet_lower:
                    relevance_score += 0.05
            
            # Boost for advanced search depth results
            if candidate.get("search_depth") == "advanced":
                relevance_score += 0.05
            
            # Penalty for generic event listing pages
            if any(term in title_lower for term in ["events calendar", "things to do", "what's on"]):
                relevance_score -= 0.2
            
            # Update score
            candidate["relevance_score"] = min(max(relevance_score, 0), 1.0)
        
        # Sort by new relevance score
        candidates.sort(key=lambda x: x.get("relevance_score", x["score"]), reverse=True)
        
        return candidates

# Standalone function for integration
def search_with_tavily(query: str, 
                      profile: Dict[str, Any],
                      date_from: datetime = None,
                      date_to: datetime = None) -> List[Dict[str, Any]]:
    """Search for events using Tavily with user profile."""
    
    agent = ResearcherAgent()
    
    # Extract from profile
    domains = profile.get("allowlist_domains", [])
    keywords = profile.get("keywords", [])
    location = profile.get("location_preference", "NYC")
    
    # Search with multi-search
    candidates = agent.search_events(
        query=query,
        keywords=keywords,
        domains=domains,
        location=location,
        date_from=date_from,
        date_to=date_to
    )
    
    return candidates

# Test function
def test_researcher():
    """Test the Researcher with multi-search capabilities."""
    print("Testing Researcher Agent (Multi-Search)")
    print("=" * 50)
    
    # Initialize agent
    agent = ResearcherAgent()
    
    # Test search parameters
    test_query = "protests political events cultural activities"
    test_keywords = ["climate", "protest", "march", "art", "festival"]
    test_domains = ["timeout.com", "nyc.gov", "eventbrite.com", "twitter.com"]
    
    print(f"\nTest Query: {test_query}")
    print(f"Keywords: {test_keywords}")
    print(f"Preferred Domains: {test_domains}")
    print(f"Excluded: Facebook domains")
    
    print("\n" + "="*50)
    print("WARNING: This will use 2 Tavily search credits")
    print("="*50)
    
    input("\nPress Enter to continue with multi-search or Ctrl+C to cancel...")
    
    # Execute multi-search
    results = agent.search_events(
        query=test_query,
        keywords=test_keywords,
        domains=test_domains,
        location="NYC",
        date_from=datetime.now(),
        date_to=datetime.now() + timedelta(days=30),
        max_results=10
    )
    
    print(f"\n" + "="*50)
    print(f"SEARCH RESULTS")
    print(f"="*50)
    print(f"Total unique results: {len(results)}")
    
    # Check for Facebook results
    facebook_count = sum(1 for r in results if "facebook" in r["url"].lower())
    print(f"Facebook results: {facebook_count} (should be 0)")
    
    # Display top results
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url'][:60]}...")
        print(f"   Score: {result.get('relevance_score', result['score']):.3f}")
        print(f"   Depth: {result.get('search_depth', 'basic')}")
        print(f"   Snippet: {result['snippet'][:150]}...")
    
    # Show domain distribution
    print("\n" + "="*50)
    print("DOMAIN DISTRIBUTION")
    print("="*50)
    
    domain_counts = {}
    for result in results:
        domain = result["url"].split("/")[2] if "/" in result["url"] else "unknown"
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{domain}: {count} results")

if __name__ == "__main__":
    # Only run test if we have an API key
    if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
        test_researcher()
    else:
        print("Please set TAVILY_API_KEY in .env file to test the Researcher")