"""Tavily Search API client with cost tracking and caching."""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import hashlib
import json

from tavily import TavilyClient as TavilyAPI

logger = logging.getLogger(__name__)


class TavilyClient:
    """Client for Tavily search API with enhanced features."""
    
    # Cost per search (as of 2025)
    SEARCH_COST = 0.001  # $1 per 1000 searches
    
    def __init__(self, use_cache: bool = True):
        """Initialize Tavily client.
        
        Args:
            use_cache: Whether to cache search results
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        
        self.client = TavilyAPI(api_key=api_key)
        self.use_cache = use_cache
        
        # Cost tracking
        self.total_searches = 0
        self.total_cost = 0.0
        
        # Performance tracking
        self.total_time = 0.0
        self.errors = []
        
        # Cache setup
        if self.use_cache:
            self._init_cache()
        
        logger.info("TavilyClient initialized")
    
    def _init_cache(self):
        """Initialize cache directory."""
        from src.config import PROJECT_ROOT
        
        self.cache_dir = PROJECT_ROOT / "cache" / "v0.4.0" / "tavily"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key from search parameters.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            MD5 hash as cache key
        """
        # Create stable string from parameters
        params = {"query": query, **kwargs}
        params_str = json.dumps(params, sort_keys=True)
        
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached search results.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached results or None
        """
        if not self.use_cache:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check cache age (1 hour TTL)
                cached_time = datetime.fromisoformat(data['timestamp'])
                age = (datetime.now() - cached_time).total_seconds()
                
                if age < 3600:  # 1 hour
                    logger.info(f"Cache hit for search (age: {age:.0f}s)")
                    return data['results']
                else:
                    logger.info(f"Cache expired for search (age: {age:.0f}s)")
                    
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, results: Dict[str, Any]):
        """Save search results to cache.
        
        Args:
            cache_key: Cache key
            results: Search results
        """
        if not self.use_cache:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Saved search results to cache")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """Search using Tavily API.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results
            include_domains: List of domains to search
            exclude_domains: List of domains to exclude
            include_answer: Include AI-generated answer
            include_raw_content: Include raw page content
            retry_count: Number of retries on failure
            
        Returns:
            Dictionary with search results and metadata
        """
        # Check cache first
        cache_key = self._get_cache_key(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            # Don't count cost for cached results
            return cached_results
        
        # Build search parameters
        params = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content
        }
        
        if include_domains:
            params["include_domains"] = include_domains
        
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        
        # Retry logic
        last_error = None
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                # Make API call
                raw_results = self.client.search(**params)
                
                elapsed = time.time() - start_time
                
                # Track metrics
                self.total_searches += 1
                self.total_cost += self.SEARCH_COST
                self.total_time += elapsed
                
                # Process results
                results = self._process_results(raw_results, query, elapsed)
                
                # Cache results
                self._save_to_cache(cache_key, results)
                
                logger.info(
                    f"Tavily search completed: {len(results['results'])} results, "
                    f"${self.SEARCH_COST:.4f} cost, {elapsed:.2f}s"
                )
                
                return results
                
            except Exception as e:
                last_error = e
                self.errors.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "query": query,
                    "attempt": attempt + 1
                })
                
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Tavily search failed (attempt {attempt + 1}/{retry_count}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Tavily search failed after {retry_count} attempts: {e}")
        
        # All retries failed
        raise Exception(f"Tavily search failed after {retry_count} attempts: {last_error}")
    
    def _process_results(
        self, 
        raw_results: Dict[str, Any], 
        query: str,
        elapsed: float
    ) -> Dict[str, Any]:
        """Process raw Tavily results into structured format.
        
        Args:
            raw_results: Raw API response
            query: Original query
            elapsed: Search time
            
        Returns:
            Processed results
        """
        results = []
        
        for item in raw_results.get("results", []):
            result = {
                "url": item.get("url"),
                "title": item.get("title"),
                "content": item.get("content"),
                "score": item.get("score", 0),
                "published_date": item.get("published_date"),
                "domain": self._extract_domain(item.get("url", ""))
            }
            
            # Add raw content if available
            if "raw_content" in item:
                result["raw_content"] = item["raw_content"]
            
            results.append(result)
        
        return {
            "query": query,
            "results": results,
            "answer": raw_results.get("answer"),
            "result_count": len(results),
            "search_time": elapsed,
            "cost": self.SEARCH_COST,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: Full URL
            
        Returns:
            Domain name
        """
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def batch_search(
        self,
        queries: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Perform multiple searches.
        
        Args:
            queries: List of search queries
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        results = []
        
        for i, query in enumerate(queries):
            logger.info(f"Processing batch search {i+1}/{len(queries)}: {query}")
            
            try:
                result = self.search(query, **kwargs)
                results.append(result)
                
                # Small delay to avoid rate limiting
                if i < len(queries) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Batch search {i+1} failed: {e}")
                results.append({
                    "query": query,
                    "error": str(e),
                    "results": [],
                    "cost": 0
                })
        
        return results
    
    def search_event_evidence(
        self,
        event_description: str,
        location: str = "New York City",
        date_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized search for event evidence.
        
        Args:
            event_description: Description of the event
            location: Event location
            date_range: Optional date range
            
        Returns:
            Search results optimized for event extraction
        """
        # Build optimized query for event search
        query_parts = [event_description, location]
        
        if date_range:
            query_parts.append(date_range)
        
        query = " ".join(query_parts)
        
        # Search with event-optimized parameters
        return self.search(
            query=query,
            search_depth="advanced",  # Use advanced for better event info
            max_results=15,  # More results for better coverage
            include_answer=True,  # Get AI summary
            include_raw_content=True  # Get full content for extraction
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_searches": self.total_searches,
            "total_cost": self.total_cost,
            "total_time": self.total_time,
            "avg_time_per_search": (
                self.total_time / self.total_searches 
                if self.total_searches > 0 else 0
            ),
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else [],
            "cache_enabled": self.use_cache
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.total_searches = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.errors = []
        logger.info("TavilyClient metrics reset")
    
    def clear_cache(self):
        """Clear all cached searches."""
        if not self.use_cache:
            return
        
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self._init_cache()
            logger.info("Tavily cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def __str__(self) -> str:
        """String representation."""
        return (f"TavilyClient(searches={self.total_searches}, "
                f"cost=${self.total_cost:.4f})")
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"TavilyClient(searches={self.total_searches}, "
                f"cost=${self.total_cost:.4f}, "
                f"avg_time={self.total_time/self.total_searches if self.total_searches else 0:.2f}s, "
                f"cache={self.use_cache})")


# Singleton instance for shared use
_default_client = None

def get_tavily_client(use_cache: bool = True) -> TavilyClient:
    """Get or create default Tavily client.
    
    Args:
        use_cache: Whether to use caching
        
    Returns:
        TavilyClient instance
    """
    global _default_client
    
    if _default_client is None:
        _default_client = TavilyClient(use_cache=use_cache)
    
    return _default_client