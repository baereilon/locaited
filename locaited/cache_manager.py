"""Cache manager for LocAIted to save API credits."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import pickle

from config import PROJECT_ROOT

class CacheManager:
    """Manages caching for API calls to save credits."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = cache_dir or PROJECT_ROOT / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        # Separate directories for different cache types
        self.search_cache_dir = self.cache_dir / "search"
        self.extract_cache_dir = self.cache_dir / "extract"
        self.llm_cache_dir = self.cache_dir / "llm"
        
        for dir in [self.search_cache_dir, self.extract_cache_dir, self.llm_cache_dir]:
            dir.mkdir(exist_ok=True)
    
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate a unique cache key from input data."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid based on TTL."""
        if not cache_file.exists():
            return False
        
        # Check file age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - file_time
        
        return age < self.ttl
    
    def get_search_cache(self, 
                        query: str, 
                        keywords: List[str], 
                        domains: List[str],
                        location: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results if available.
        
        Args:
            query: Search query
            keywords: Keywords list
            domains: Domains list
            location: Location string
            
        Returns:
            Cached results or None
        """
        cache_data = {
            "query": query,
            "keywords": sorted(keywords[:10]),  # Limit and sort for consistency
            "domains": sorted(domains[:10]),
            "location": location
        }
        
        cache_key = self._generate_cache_key(cache_data)
        cache_file = self.search_cache_dir / f"{cache_key}.pkl"
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                print(f"Cache hit for search: {cache_key}")
                return cached['results']
            except Exception as e:
                print(f"Cache read error: {e}")
                return None
        
        return None
    
    def save_search_cache(self,
                         query: str,
                         keywords: List[str],
                         domains: List[str],
                         location: str,
                         results: List[Dict[str, Any]]):
        """Save search results to cache."""
        cache_data = {
            "query": query,
            "keywords": sorted(keywords[:10]),
            "domains": sorted(domains[:10]),
            "location": location
        }
        
        cache_key = self._generate_cache_key(cache_data)
        cache_file = self.search_cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'cache_key': cache_key,
                    'timestamp': datetime.now(),
                    'query_params': cache_data,
                    'results': results
                }, f)
            print(f"Cached search results: {cache_key}")
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def get_extract_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached extraction for a URL."""
        cache_key = self._generate_cache_key({"url": url})
        cache_file = self.extract_cache_dir / f"{cache_key}.json"
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                print(f"Cache hit for extract: {url[:50]}...")
                return cached['extracted']
            except Exception as e:
                print(f"Cache read error: {e}")
                return None
        
        return None
    
    def save_extract_cache(self, url: str, extracted: Dict[str, Any]):
        """Save extraction result to cache."""
        cache_key = self._generate_cache_key({"url": url})
        cache_file = self.extract_cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'extracted': extracted
                }, f, indent=2)
            print(f"Cached extraction for: {url[:50]}...")
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def get_llm_cache(self, 
                     events: List[Dict[str, Any]], 
                     user_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached LLM scoring results."""
        # Create cache key from events and profile
        cache_data = {
            "events": [
                {
                    "title": e.get("title"),
                    "location": e.get("location"),
                    "summary": e.get("summary", "")[:100]
                } 
                for e in events
            ],
            "interests": user_profile.get("interest_areas", []),
            "keywords": sorted(user_profile.get("keywords", [])[:10])
        }
        
        cache_key = self._generate_cache_key(cache_data)
        cache_file = self.llm_cache_dir / f"{cache_key}.json"
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                print(f"Cache hit for LLM scoring: {cache_key}")
                return cached['result']
            except Exception as e:
                print(f"Cache read error: {e}")
                return None
        
        return None
    
    def save_llm_cache(self,
                      events: List[Dict[str, Any]],
                      user_profile: Dict[str, Any],
                      result: Dict[str, Any]):
        """Save LLM scoring result to cache."""
        cache_data = {
            "events": [
                {
                    "title": e.get("title"),
                    "location": e.get("location"),
                    "summary": e.get("summary", "")[:100]
                } 
                for e in events
            ],
            "interests": user_profile.get("interest_areas", []),
            "keywords": sorted(user_profile.get("keywords", [])[:10])
        }
        
        cache_key = self._generate_cache_key(cache_data)
        cache_file = self.llm_cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'cache_params': cache_data,
                    'result': result
                }, f, indent=2)
            print(f"Cached LLM scoring: {cache_key}")
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def clear_expired_cache(self):
        """Remove expired cache entries."""
        removed_count = 0
        
        for cache_dir in [self.search_cache_dir, self.extract_cache_dir, self.llm_cache_dir]:
            for cache_file in cache_dir.glob("*"):
                if not self._is_cache_valid(cache_file):
                    try:
                        cache_file.unlink()
                        removed_count += 1
                    except Exception as e:
                        print(f"Error removing cache file {cache_file}: {e}")
        
        if removed_count > 0:
            print(f"Removed {removed_count} expired cache entries")
        
        return removed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage."""
        stats = {
            "search_entries": len(list(self.search_cache_dir.glob("*.pkl"))),
            "extract_entries": len(list(self.extract_cache_dir.glob("*.json"))),
            "llm_entries": len(list(self.llm_cache_dir.glob("*.json"))),
            "total_size_mb": 0
        }
        
        # Calculate total cache size
        for cache_dir in [self.search_cache_dir, self.extract_cache_dir, self.llm_cache_dir]:
            for file in cache_dir.glob("*"):
                stats["total_size_mb"] += file.stat().st_size / (1024 * 1024)
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats


def test_cache_manager():
    """Test the cache manager."""
    print("Testing Cache Manager")
    print("=" * 50)
    
    cache = CacheManager(ttl_hours=1)  # Short TTL for testing
    
    # Test search cache
    print("\n1. Testing search cache:")
    
    # Check for cached results (should be None)
    cached = cache.get_search_cache(
        query="test query",
        keywords=["keyword1", "keyword2"],
        domains=["domain1.com", "domain2.com"],
        location="NYC"
    )
    print(f"   Initial cache check: {cached}")
    
    # Save to cache
    test_results = [
        {"url": "http://example.com", "title": "Test Event", "score": 0.8}
    ]
    cache.save_search_cache(
        query="test query",
        keywords=["keyword1", "keyword2"],
        domains=["domain1.com", "domain2.com"],
        location="NYC",
        results=test_results
    )
    
    # Check cache again (should return results)
    cached = cache.get_search_cache(
        query="test query",
        keywords=["keyword1", "keyword2"],
        domains=["domain1.com", "domain2.com"],
        location="NYC"
    )
    print(f"   After caching: {cached}")
    
    # Test extract cache
    print("\n2. Testing extract cache:")
    
    test_url = "http://example.com/event"
    extracted_data = {
        "title": "Test Event",
        "location": "NYC",
        "time": "2025-01-01"
    }
    
    # Check cache (should be None)
    cached = cache.get_extract_cache(test_url)
    print(f"   Initial cache check: {cached}")
    
    # Save to cache
    cache.save_extract_cache(test_url, extracted_data)
    
    # Check again (should return data)
    cached = cache.get_extract_cache(test_url)
    print(f"   After caching: {cached}")
    
    # Test LLM cache
    print("\n3. Testing LLM cache:")
    
    test_events = [{"title": "Event 1", "location": "NYC", "summary": "Test"}]
    test_profile = {
        "interest_areas": ["protests"],
        "keywords": ["climate", "activism"]
    }
    test_result = {"scores": [0.8], "cost": 0.001}
    
    # Check cache (should be None)
    cached = cache.get_llm_cache(test_events, test_profile)
    print(f"   Initial cache check: {cached}")
    
    # Save to cache
    cache.save_llm_cache(test_events, test_profile, test_result)
    
    # Check again (should return result)
    cached = cache.get_llm_cache(test_events, test_profile)
    print(f"   After caching: {cached}")
    
    # Get cache stats
    print("\n4. Cache statistics:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Cache manager test complete!")


if __name__ == "__main__":
    test_cache_manager()