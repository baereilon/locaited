"""The Fact-Checker for LocAIted - LLM-based deduplication and event extraction."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
from tavily import TavilyClient
from openai import OpenAI
import re
import sys
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TAVILY_API_KEY, OPENAI_API_KEY, OPENAI_MODEL, PROJECT_ROOT

# v0.3.0: Default max extractions increased
TAVILY_EXTRACT_MAX_URLS = 20
from cache_manager import CacheManager

class FactCheckerAgent:
    """The Fact-Checker: Like a newsroom fact-checker, verifies and deduplicates events."""
    
    def __init__(self, api_key: str = TAVILY_API_KEY, use_cache: bool = True):
        """Initialize Tavily and OpenAI clients."""
        self.tavily_client = TavilyClient(api_key=api_key)
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.results_dir = PROJECT_ROOT / "extraction_results"
        self.results_dir.mkdir(exist_ok=True)
        self.use_cache = use_cache
        self.cache = CacheManager() if use_cache else None
        self.model = OPENAI_MODEL
        
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a single URL using Tavily extract API.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted content with raw response saved
        """
        # Check cache first
        if self.use_cache and self.cache:
            cached = self.cache.get_extract_cache(url)
            if cached:
                print(f"Using cached extraction for: {url[:50]}... (saved API credit)")
                return cached
        
        try:
            print(f"Extracting from: {url[:80]}...")
            
            # Call Tavily extract API
            response = self.tavily_client.extract(url)
            
            # Save raw response for inspection
            self.save_extraction_result(url, response)
            
            # Save to cache
            if self.use_cache and self.cache:
                self.cache.save_extract_cache(url, response)
            
            return response
            
        except Exception as e:
            print(f"Error extracting from {url[:50]}: {e}")
            return {"error": str(e), "url": url}
    
    def save_extraction_result(self, url: str, response: Dict[str, Any]):
        """Save extraction result to JSON file for inspection."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename from URL (sanitized)
        url_slug = re.sub(r'[^\w\-_]', '_', url.split('/')[-1])[:50]
        filename = f"extract_{timestamp}_{url_slug}.json"
        
        filepath = self.results_dir / filename
        
        # Save with metadata
        result_data = {
            "timestamp": timestamp,
            "url": url,
            "response": response,
            "cost": 0.01  # 1 credit per extraction
        }
        
        with open(filepath, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        
        print(f"Saved extraction to: {filepath.name}")
    
    def llm_extract_and_deduplicate(self, candidates: List[Dict[str, Any]], 
                                   extracted_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use LLM to extract structured event data and deduplicate.
        
        Args:
            candidates: Original search candidates
            extracted_content: Raw extraction results from Tavily
            
        Returns:
            List of unique, structured events
        """
        # Prepare content for LLM
        events_data = []
        for i, (candidate, extraction) in enumerate(zip(candidates, extracted_content)):
            # Get raw text from extraction
            raw_text = ""
            if "results" in extraction and extraction["results"]:
                result = extraction["results"][0] if isinstance(extraction["results"], list) else extraction["results"]
                raw_text = result.get("raw_content", "") or result.get("content", "")
            
            event_info = {
                "id": i + 1,
                "url": candidate["url"],
                "title": candidate.get("title", "Unknown"),
                "snippet": candidate.get("snippet", "")[:200],
                "raw_text": raw_text[:1000],  # Limit to reduce tokens
                "published_date": candidate.get("published_date", "")
            }
            events_data.append(event_info)
        
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(events_data)
        
        try:
            print(f"Calling {self.model} for event extraction and deduplication...")
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker. Extract event information and identify duplicates. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            if content.startswith('['):
                json_str = content
            else:
                # Find JSON array in response
                start = content.find('[')
                end = content.rfind(']') + 1
                json_str = content[start:end]
            
            events = json.loads(json_str)
            
            # Save LLM response
            self._save_llm_extraction(prompt, content, events, response.usage.dict())
            
            return events
            
        except Exception as e:
            print(f"LLM extraction error: {e}")
            # Fallback to basic extraction
            return self._fallback_extraction(candidates, extracted_content)
    
    def _build_extraction_prompt(self, events_data: List[Dict[str, Any]]) -> str:
        """Build prompt for LLM extraction and deduplication."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are a newsroom fact-checker verifying event information for photojournalists.

CURRENT DATE: {current_date}

PRIMARY TASK: Extract unique events with complete, actionable information that photographers can use to plan their coverage.

EVENTS TO PROCESS:
{json.dumps(events_data, indent=2)}

EXTRACTION REQUIREMENTS:
- title: Clear, descriptive event title (not just article headline)
- date: Event date in YYYY-MM-DD format (CRITICAL - extract from content, not just "Monday")
- time: Event time in HH:MM format (CRITICAL - photographers need to plan arrival)
- location: SPECIFIC address with street/avenue in NYC (e.g., "Bryant Park, 42nd St & 6th Ave")
- organizer: Who is organizing the event
- access_req: "open to all" | "press card required" | "registration required" | "paid admission" | "unknown"
- summary: 1-2 sentence description focusing on visual/newsworthy aspects
- has_basic_info: true ONLY if has ALL of: specific date, time, and street address
- is_duplicate_of: ID of the first occurrence if duplicate, null otherwise
- is_past_event: true if event date is before {current_date}
- is_non_event: true if this is a profile page, calendar listing, or article about past events
- source_url: Original URL

AGGRESSIVE DEDUPLICATION RULES:
1. EXACT DUPLICATES: Same event name + same date = mark as duplicate
2. SIMILAR EVENTS: Events with similar titles at same venue within 3 days = likely same event
3. SOCIAL MEDIA PAGES: Multiple URLs for same Twitter/Instagram account = keep only one
4. EVENT SERIES: "March with X at Y Parade" variations = likely same parade, keep most complete
5. NEWS COVERAGE: Multiple articles about same past event = keep only one
6. NORMALIZE TITLES: Ignore "the", punctuation, capitalization when comparing

WHEN MERGING DUPLICATES:
- Keep the MOST GENERAL version as the primary record
- Prefer "Met Gala 2025" over "Met Gala musicians highlights"
- Prefer "Israel Day Parade" over "March with MJE at Israel Day Parade"
- Prefer official event names over specific sub-events or perspectives
- Merge the best information from all duplicates into the general version

EXAMPLES OF DUPLICATES TO CATCH:
- "Met Gala 2025" vs "Met Gala musicians highlights" = KEEP "Met Gala 2025"
- "Israel Day Parade" vs "March with MJE | Israel Day Parade" = KEEP "Israel Day Parade"
- "Climate March NYC" vs "Students join Climate March" = KEEP "Climate March NYC"
- "@protest_nyc" vs "PRO_NYC (@protest_nyc)" = KEEP ONE

Return ONLY a JSON array with extracted events:
[
  {{
    "id": 1,
    "title": "Climate Justice March at Bryant Park",
    "date": "2025-04-15",
    "time": "14:00",
    "location": "Bryant Park, 42nd St & 6th Ave, NYC",
    "organizer": "NYC Climate Coalition",
    "access_req": "open to all",
    "summary": "Large-scale climate protest demanding policy changes from city government.",
    "has_basic_info": true,
    "is_duplicate_of": null,
    "is_past_event": false,
    "source_url": "https://..."
  }},
  ...
]

JSON array only:"""
        
        return prompt
    
    def _save_llm_extraction(self, prompt: str, response: str, parsed: Any, usage: Dict):
        """Save LLM extraction for inspection."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_extraction_{timestamp}.json"
        filepath = self.results_dir / filename
        
        data = {
            "timestamp": timestamp,
            "model": self.model,
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "raw_response": response,
            "parsed_events": parsed,
            "token_usage": usage,
            "estimated_cost": (usage.get("prompt_tokens", 0) * 0.15 + usage.get("completion_tokens", 0) * 0.60) / 1_000_000
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"LLM extraction saved to: {filepath.name}")
    
    def _fallback_extraction(self, candidates: List[Dict[str, Any]], 
                           extracted_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback extraction without LLM."""
        events = []
        seen_titles = set()
        
        for candidate, extraction in zip(candidates, extracted_content):
            # Get basic info from candidate
            title = candidate.get("title", "Unknown Event")
            
            # Simple deduplication
            title_key = title.lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            # Extract raw text
            raw_text = ""
            if "results" in extraction and extraction["results"]:
                result = extraction["results"][0] if isinstance(extraction["results"], list) else extraction["results"]
                raw_text = result.get("raw_content", "") or result.get("content", "")
            
            # Basic extraction
            event = {
                "id": len(events) + 1,
                "title": title,
                "date": None,
                "time": None,
                "location": "NYC",
                "organizer": "Unknown",
                "access_req": "unknown",
                "summary": candidate.get("snippet", "")[:200],
                "has_basic_info": False,
                "is_duplicate_of": None,
                "is_past_event": False,
                "source_url": candidate["url"]
            }
            
            # Try to extract date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', raw_text)
            if date_match:
                event["date"] = date_match.group(1)
                # Check if past
                try:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d")
                    event["is_past_event"] = event_date < datetime.now()
                except:
                    pass
            
            # Check for basic info
            event["has_basic_info"] = bool(event["title"] and (event["date"] or event["location"] != "NYC"))
            
            events.append(event)
        
        return events
    
    def extract_event(self, url: str, title: str = "Unknown", score: float = 0.5) -> Dict[str, Any]:
        """
        Extract and structure a single event (backward compatibility).
        
        Args:
            url: URL to extract
            title: Event title from search
            score: Relevance score from search
            
        Returns:
            Structured event data
        """
        extraction = self.extract_from_url(url)
        
        # Use fallback extraction for single event
        candidates = [{"url": url, "title": title, "score": score, "snippet": ""}]
        events = self._fallback_extraction(candidates, [extraction])
        
        return events[0] if events else {
            "title": title,
            "url": url,
            "location": "NYC",
            "access_req": "unknown",
            "summary": "",
            "has_basic_info": False
        }
    
    def extract_from_candidates(self, 
                               candidates: List[Dict[str, Any]], 
                               max_extractions: int = 20,  # v0.3.0: Increased from 5
                               use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        Extract detailed information from candidate URLs with LLM deduplication.
        
        Args:
            candidates: List of candidate URLs from Researcher
            max_extractions: Maximum number of URLs to extract (cost limit)
            use_llm: Whether to use LLM for extraction/deduplication
            
        Returns:
            List of unique, structured events (no artificial limit on output count)
        """
        # Sort by score to extract best candidates first
        sorted_candidates = sorted(candidates, 
                                  key=lambda x: x.get("relevance_score", x.get("score", 0)), 
                                  reverse=True)
        
        # Extract from top candidates
        extracted_content = []
        for candidate in sorted_candidates[:max_extractions]:
            url = candidate.get("url")
            if not url:
                continue
            
            extraction = self.extract_from_url(url)
            extracted_content.append(extraction)
        
        # Use LLM for structured extraction and deduplication
        if use_llm and OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            events = self.llm_extract_and_deduplicate(
                sorted_candidates[:max_extractions], 
                extracted_content
            )
        else:
            # Fallback to basic extraction
            events = self._fallback_extraction(
                sorted_candidates[:max_extractions],
                extracted_content
            )
        
        # Filter out duplicates and non-events (v0.3.0)
        unique_events = []
        for event in events:
            # Skip if it's marked as duplicate
            if event.get("is_duplicate_of") is not None:
                continue
            # Skip if it's a non-event (profile page, calendar, etc.)
            if event.get("is_non_event", False):
                continue
            unique_events.append(event)
        
        # Save summary
        self.save_extraction_summary(unique_events)
        
        print(f"\nExtracted {len(unique_events)} unique events from {len(candidates)} candidates")
        if use_llm:
            duplicates = len([e for e in events if e.get("is_duplicate_of")])
            past = len([e for e in events if e.get("is_past_event")])
            print(f"Removed {duplicates} duplicates, flagged {past} past events")
        
        return unique_events
    
    def save_extraction_summary(self, events: List[Dict[str, Any]]):
        """Save a summary of all extracted events."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.results_dir / f"extraction_summary_{timestamp}.json"
        
        # Calculate stats
        has_basic = len([e for e in events if e.get("has_basic_info")])
        past_events = len([e for e in events if e.get("is_past_event")])
        
        summary = {
            "timestamp": timestamp,
            "total_events": len(events),
            "events_with_basic_info": has_basic,
            "past_events": past_events,
            "basic_info_percentage": (has_basic / len(events) * 100) if events else 0,
            "events": events
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\nExtraction summary saved to: {summary_file.name}")
        print(f"Total unique events: {len(events)}")
        print(f"Events with basic info: {has_basic} ({summary['basic_info_percentage']:.1f}%)")
        print(f"Past events flagged: {past_events}")

# Test function
def test_fact_checker():
    """Test the Fact-Checker with real URLs."""
    print("Testing Fact-Checker Agent (with LLM deduplication)")
    print("=" * 50)
    
    # Initialize agent
    agent = FactCheckerAgent()
    
    # Test with sample candidates that might have duplicates
    test_candidates = [
        {
            "url": "https://www.timeout.com/newyork/news/these-are-nycs-top-spring-2025-events",
            "title": "NYC Spring Events 2025 - TimeOut",
            "snippet": "The best events happening in NYC this spring...",
            "score": 0.8
        },
        {
            "url": "https://www.nyc.gov/office-of-the-mayor/news",
            "title": "NYC Mayor's Office News",
            "snippet": "Latest news and events from the Mayor's office...",
            "score": 0.6
        },
        {
            "url": "https://www.eventbrite.com/d/ny--new-york/events/",
            "title": "NYC Events - Eventbrite",
            "snippet": "Discover events happening in New York City...",
            "score": 0.7
        }
    ]
    
    print("\nTest Candidates:")
    for i, c in enumerate(test_candidates, 1):
        print(f"  {i}. {c['title']}")
        print(f"     URL: {c['url'][:60]}...")
    
    print("\n" + "="*50)
    print("WARNING: This test will use:")
    print("  - 3 Tavily extract credits")
    print("  - ~$0.001 OpenAI credits (for LLM extraction)")
    print("="*50)
    
    input("\nPress Enter to continue with extraction or Ctrl+C to cancel...")
    
    # Extract from candidates with LLM
    events = agent.extract_from_candidates(test_candidates, max_extractions=3, use_llm=True)
    
    print("\n" + "=" * 50)
    print("EXTRACTION RESULTS")
    print("=" * 50)
    
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Date: {event.get('date', 'Not found')}")
        print(f"   Location: {event.get('location', 'Unknown')}")
        print(f"   Organizer: {event.get('organizer', 'Unknown')}")
        print(f"   Access: {event['access_req']}")
        print(f"   Has Basic Info: {event.get('has_basic_info', False)}")
        print(f"   Is Past Event: {event.get('is_past_event', False)}")
        print(f"   Summary: {event.get('summary', '')[:100]}...")
        print(f"   URL: {event['source_url'][:60]}...")
    
    print(f"\nResults saved in: {agent.results_dir}")
    print("Check extraction_results/ folder for detailed JSON files")

if __name__ == "__main__":
    # Only run test if API keys are available
    if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
        if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            test_fact_checker()
        else:
            print("OpenAI API key not set - running without LLM extraction")
            agent = FactCheckerAgent()
            # Test without LLM
            test_candidates = [
                {
                    "url": "https://www.timeout.com/newyork/news",
                    "title": "NYC Events",
                    "snippet": "Events in NYC...",
                    "score": 0.8
                }
            ]
            events = agent.extract_from_candidates(test_candidates, max_extractions=1, use_llm=False)
            print(f"Extracted {len(events)} events without LLM")
    else:
        print("Please set TAVILY_API_KEY in .env file to test the Fact-Checker")