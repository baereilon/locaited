"""The Editor - Plans coverage strategy and manages the news team's focus areas."""

import pandas as pd
from typing import List, Dict, Any, Set
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TEST_DATA_PATH

class EditorAgent:
    """The Editor: Like a newsroom editor, decides what stories to pursue and assigns coverage areas."""
    
    def __init__(self, test_data_path: Path = TEST_DATA_PATH):
        """Initialize with path to test data."""
        self.test_data_path = test_data_path
        self.test_events = None
        self.domains_extracted = set()
        self.keywords_extracted = set()
        
    def load_test_data(self) -> pd.DataFrame:
        """Load and parse the test CSV data."""
        if self.test_events is None:
            self.test_events = pd.read_csv(self.test_data_path)
            # Clean column names (remove trailing spaces)
            self.test_events.columns = self.test_events.columns.str.strip()
            print(f"Loaded {len(self.test_events)} test events")
        return self.test_events
    
    def extract_domains_from_events(self) -> Set[str]:
        """Extract unique domains from test event URLs - identifies trusted sources."""
        df = self.load_test_data()
        domains = set()
        
        # Base domains that might appear
        base_domains = {
            "cnn.com", "nytimes.com", "bbc.com", "reuters.com", "apnews.com",
            "un.org", "whitehouse.gov", "state.gov", "nyc.gov",
            "instagram.com", "twitter.com", "facebook.com",
            "eventbrite.com", "timeout.com"
        }
        
        # Extract from URLs if URL column exists
        if 'URL' in df.columns:
            for url in df['URL'].dropna():
                try:
                    parsed = urlparse(str(url))
                    domain = parsed.netloc.lower()
                    # Clean up domain
                    domain = domain.replace('www.', '')
                    if domain:
                        domains.add(domain)
                except:
                    pass
        
        # Add base domains
        domains.update(base_domains)
        self.domains_extracted = domains
        return domains
    
    def extract_keywords_from_events(self) -> List[str]:
        """Extract keywords from event descriptions - determines coverage priorities."""
        df = self.load_test_data()
        keywords = set()
        
        # Extract from Event Name
        if 'Event Name' in df.columns:
            for event_name in df['Event Name'].dropna():
                # Extract significant words (3+ chars, not common words)
                words = re.findall(r'\b[a-z]+\b', str(event_name).lower())
                keywords.update([w for w in words if len(w) > 3])
        
        # Extract from Event type
        if 'Event type' in df.columns:
            for event_type in df['Event type'].dropna():
                keywords.add(str(event_type).lower())
        
        # Add standard keywords
        standard_keywords = {
            "protest", "march", "rally", "demonstration",
            "parade", "festival", "celebration", "cultural",
            "conference", "summit", "meeting", "assembly",
            "press", "mayor", "council", "political",
            "gala", "opening", "museum", "fashion"
        }
        keywords.update(standard_keywords)
        
        # Remove common words
        stop_words = {"with", "from", "this", "that", "have", "been", "will", "event"}
        keywords = keywords - stop_words
        
        self.keywords_extracted = list(keywords)
        return self.keywords_extracted
    
    def extract_interest_areas(self) -> List[str]:
        """Extract interest areas from test data - defines newsroom beats."""
        df = self.load_test_data()
        interests = set()
        
        # Extract from Event type column
        if 'Event type' in df.columns:
            interests.update(df['Event type'].dropna().unique())
        
        # Map to standard categories
        interest_mapping = {
            "protest": "Political event",
            "parade": "Cultural Event",
            "conference": "Political event",
            "gala": "Cultural Event",
            "news": "News"
        }
        
        # Normalize interests
        normalized = set()
        for interest in interests:
            interest_lower = str(interest).lower()
            for key, value in interest_mapping.items():
                if key in interest_lower:
                    normalized.add(value)
                    break
            else:
                normalized.add(str(interest))
        
        return list(normalized)
    
    def build_user_profile(self, 
                          user_interests: List[str] = None,
                          user_credentials: List[str] = None) -> Dict[str, Any]:
        """Build coverage profile from test data - determines what the newsroom should focus on."""
        
        # Extract from test data
        domains = self.extract_domains_from_events()
        keywords = self.extract_keywords_from_events()
        interests = self.extract_interest_areas()
        
        # Build profile - like an editor's coverage plan
        profile = {
            "allowlist_domains": list(domains),
            "keywords": keywords,
            "interest_areas": interests if not user_interests else user_interests,
            "credentials": user_credentials if user_credentials else ["press_card"],
            "location_preference": "NYC",
            "prior_feedback": []  # Would store user feedback over time
        }
        
        return profile
    
    def plan_search_strategy(self, profile: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Plan research strategy - like an editor assigning beats to reporters."""
        
        # Analyze query to determine search approach
        query_lower = query.lower()
        
        # Determine search type
        search_type = "general"
        if "protest" in query_lower or "demonstration" in query_lower:
            search_type = "breaking_news"
        elif "parade" in query_lower or "festival" in query_lower:
            search_type = "scheduled_event"
        elif "un" in query_lower or "assembly" in query_lower:
            search_type = "diplomatic"
        elif "mayor" in query_lower or "council" in query_lower:
            search_type = "political"
        
        # Select relevant keywords based on query
        relevant_keywords = [k for k in profile["keywords"] 
                           if k in query_lower or query_lower in k]
        
        # If no matches, use top keywords
        if not relevant_keywords:
            relevant_keywords = profile["keywords"][:10]
        
        # Select domains based on search type
        if search_type == "breaking_news":
            priority_domains = ["twitter.com", "cnn.com", "reuters.com"]
        elif search_type == "scheduled_event":
            priority_domains = ["nyc.gov", "timeout.com", "eventbrite.com"]
        elif search_type == "diplomatic":
            priority_domains = ["un.org", "state.gov", "whitehouse.gov"]
        else:
            priority_domains = profile["allowlist_domains"][:10]
        
        strategy = {
            "search_type": search_type,
            "search_keywords": relevant_keywords[:15],
            "priority_domains": priority_domains,
            "search_depth": "advanced" if search_type == "scheduled_event" else "basic",
            "max_results": 20 if search_type == "breaking_news" else 15
        }
        
        return strategy

# Test the agent
def test_editor():
    """Test the Editor agent."""
    print("Testing The Editor Agent")
    print("=" * 50)
    
    agent = EditorAgent()
    
    # Test loading data
    df = agent.load_test_data()
    print(f"\n1. Loaded {len(df)} test events")
    
    # Test domain extraction
    domains = agent.extract_domains_from_events()
    print(f"\n2. Extracted {len(domains)} unique domains")
    print(f"   Sample domains: {list(domains)[:5]}")
    
    # Test keyword extraction
    keywords = agent.extract_keywords_from_events()
    print(f"\n3. Extracted {len(keywords)} keywords")
    print(f"   Sample keywords: {keywords[:10]}")
    
    # Test interest extraction
    interests = agent.extract_interest_areas()
    print(f"\n4. Identified {len(interests)} interest areas")
    print(f"   Interest areas: {interests}")
    
    # Test profile building
    profile = agent.build_user_profile()
    print(f"\n5. Built user profile:")
    print(f"   - {len(profile['allowlist_domains'])} domains")
    print(f"   - {len(profile['keywords'])} keywords")
    print(f"   - {len(profile['interest_areas'])} interest areas")
    print(f"   - Credentials: {profile['credentials']}")
    
    # Test search planning
    test_query = "Find upcoming protests in NYC"
    strategy = agent.plan_search_strategy(profile, test_query)
    print(f"\n6. Search strategy for '{test_query}':")
    print(f"   - Type: {strategy['search_type']}")
    print(f"   - Depth: {strategy['search_depth']}")
    print(f"   - Keywords: {strategy['search_keywords'][:5]}")
    print(f"   - Domains: {strategy['priority_domains'][:3]}")

if __name__ == "__main__":
    test_editor()