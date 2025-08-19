"""The Publisher for LocAIted - LLM-based scoring and recommendations."""

from typing import List, Dict, Any, Tuple, Literal
from datetime import datetime
import json
from pathlib import Path
from openai import OpenAI
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, OPENAI_MODEL, PROJECT_ROOT

class PublisherAgent:
    """LLM-based agent for scoring events and generating recommendations."""
    
    def __init__(self, model: str = OPENAI_MODEL):
        """Initialize with OpenAI client."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.results_dir = PROJECT_ROOT / "recommendation_results"
        self.results_dir.mkdir(exist_ok=True)
        self.min_viable_events = 5
        self.last_api_cost = 0.0
        
    def pre_filter_events(self, 
                         events: List[Dict[str, Any]], 
                         user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Pre-filter events using deterministic rules before LLM scoring.
        
        Args:
            events: List of extracted events
            user_profile: User preferences
            
        Returns:
            Filtered list of events
        """
        filtered = []
        credentials = user_profile.get("credentials", [])
        
        for event in events:
            access = event.get("access_req", "unknown").lower()
            
            # Skip events that require credentials user doesn't have
            if "press" in access and "press_card" not in credentials:
                continue
            if "permit" in access and not any("permit" in c for c in credentials):
                continue
                
            filtered.append(event)
        
        return filtered
    
    def build_scoring_prompt(self, 
                           events: List[Dict[str, Any]], 
                           user_profile: Dict[str, Any]) -> str:
        """
        Build prompt for LLM to score events.
        
        Args:
            events: List of events to score
            user_profile: User preferences
            
        Returns:
            Formatted prompt string
        """
        # Prepare events for prompt (limit fields to reduce tokens)
        events_data = []
        for i, event in enumerate(events, 1):
            event_summary = {
                "id": i,
                "title": event.get("title", "Unknown"),
                "date": event.get("date"),
                "time": event.get("time"),
                "location": event.get("location", "Unknown"),
                "organizer": event.get("organizer", "Unknown"),
                "access": event.get("access_req", "Unknown"),
                "has_basic_info": event.get("has_basic_info", False),
                "is_past_event": event.get("is_past_event", False),
                "summary": event.get("summary", "")[:200]  # Limit summary length
            }
            events_data.append(event_summary)
        
        prompt = f"""You are an expert event publisher for photojournalists in NYC.

YOUR PRIMARY JOB: Evaluate if this batch of events is good enough for the user, or if we need another search cycle.

USER PROFILE:
- Interests: {', '.join(user_profile.get('interest_areas', []))}
- Keywords: {', '.join(user_profile.get('keywords', [])[:10])}
- Credentials: {', '.join(user_profile.get('credentials', []))}
- Location: {user_profile.get('location_preference', 'NYC')}

GATE DECISION CRITERIA (MOST IMPORTANT):
- Are these REAL, SPECIFIC events (not profile pages or calendars)?
- Do they have actionable information for planning coverage?
- Will they interest THIS specific user based on their profile?
- Quality threshold: Need at least 3-5 high-quality matches (score >= 0.5)

SCORING CRITERIA:
1. Newsworthiness: Will this event likely be covered in news?
2. Visual Interest: Good photo opportunities?
3. Competition: Balance between importance and photographer saturation
4. Access: Can the user actually attend?
5. Interest Match: Aligns with user's interests?
6. Information Completeness: Can photographer plan their day with this info?

EVENTS TO EVALUATE:
{json.dumps(events_data, indent=2)}

TASKS (IN ORDER OF IMPORTANCE):
1. First, evaluate overall batch quality (determines if we need another cycle)
2. Score each event from 0.0 to 1.0
3. Create a CLEAR, DESCRIPTIVE title (up to 250 chars) that tells the photographer:
   - What type of event (PROTEST/CULTURAL/POLITICAL/SPORTS/COMMUNITY)
   - The specific event name and key details
   - EXACT date, time, and location
   
   Examples of GOOD titles:
   - "PROTEST: Climate Justice March for Policy Reform - April 15, 2PM at Bryant Park (42nd & 6th Ave)"
   - "CULTURAL: Met Gala 'Garden of Time' Fashion Exhibition - May 6, 6PM Red Carpet at Metropolitan Museum (5th Ave & 82nd St)"
   - "POLITICAL: Mayor Adams Town Hall on Housing Crisis - March 20, 7PM at Brooklyn Borough Hall (209 Joralemon St)"
   
   Examples of BAD titles (too vague):
   - "Events in NYC"
   - "March with MJE"
   - "@protest_nyc"

4. Provide a rationale (max 350 chars) focusing on visual opportunities and why this matters

PENALTIES:
- Past events: -0.5 to score (photographers can't cover past events!)
- Missing date/time/location: -0.3 to score
- Vague titles or non-events: -0.4 to score

Return ONLY a JSON array with this exact structure:
[
  {{
    "id": 1,
    "score": 0.75,
    "photo_title": "PROTEST: Climate March - April 15 at Bryant Park",
    "rationale": "Strong visual potential with large crowds expected. Bryant Park offers good vantage points. Medium competition from other photographers. Peak afternoon lighting."
  }},
  ...
]

JSON array only, no other text:"""
        
        return prompt
    
    def call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API for scoring.
        
        Args:
            prompt: The scoring prompt
            
        Returns:
            Parsed LLM response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert event publisher. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=1000
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            if content.startswith('['):
                json_str = content
            else:
                # Find JSON array in response
                start = content.find('[')
                end = content.rfind(']') + 1
                json_str = content[start:end]
            
            scores = json.loads(json_str)
            
            # Calculate approximate cost
            # GPT-4-mini: $0.15 per 1M input, $0.60 per 1M output
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self.last_api_cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
            
            # Save for inspection
            self.save_llm_response(prompt, content, scores, response.usage.dict())
            
            return {
                "scores": scores,
                "usage": response.usage.dict(),
                "cost": self.last_api_cost
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            # Return empty scores on parse error
            return {"scores": [], "usage": {}, "cost": 0}
        except Exception as e:
            print(f"LLM API error: {e}")
            return {"scores": [], "usage": {}, "cost": 0}
    
    def save_llm_response(self, prompt: str, response: str, parsed: Any, usage: Dict):
        """Save LLM interaction for inspection."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_scoring_{timestamp}.json"
        filepath = self.results_dir / filename
        
        data = {
            "timestamp": timestamp,
            "model": self.model,
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "full_prompt_length": len(prompt),
            "raw_response": response,
            "parsed_scores": parsed,
            "token_usage": usage,
            "estimated_cost": self.last_api_cost
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"LLM response saved to: {filepath.name}")
    
    def merge_scores_with_events(self, 
                                events: List[Dict[str, Any]], 
                                llm_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge LLM scores back with event data.
        
        Args:
            events: Original event list
            llm_scores: LLM scoring results
            
        Returns:
            Events with scores and rationales added
        """
        # Create score lookup
        score_map = {score["id"]: score for score in llm_scores}
        
        recommendations = []
        for i, event in enumerate(events, 1):
            score_data = score_map.get(i, {"score": 0.0, "rationale": "No score available"})
            
            # Use the photographer-friendly title if provided, otherwise use original
            display_title = score_data.get("photo_title", event.get("title", "Unknown Event"))
            
            recommendation = {
                **event,
                "title": display_title,  # Replace with photo-friendly title
                "original_title": event.get("title", "Unknown Event"),  # Keep original
                "recommendation": float(score_data.get("score", 0)),
                "rationale": score_data.get("rationale", "")[:350]  # Enforce limit
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def make_gate_decision(self, 
                          recommendations: List[Dict[str, Any]],
                          cycle_count: int) -> Tuple[Literal["accept", "revise"], str]:
        """
        Deterministic gate decision based on results.
        
        Args:
            recommendations: Scored events
            cycle_count: Number of cycles performed
            
        Returns:
            Tuple of (decision, notes)
        """
        # Never cycle more than 2 times
        if cycle_count >= 2:
            return "accept", "Max cycles reached"
        
        # Count viable events
        viable = [r for r in recommendations if r["recommendation"] >= 0.3]
        
        if len(viable) < self.min_viable_events:
            return "revise", f"Only {len(viable)} viable events (score >= 0.3), need {self.min_viable_events}"
        
        # Check top scores
        if recommendations and recommendations[0]["recommendation"] < 0.4:
            return "revise", "No high-confidence matches, expand search"
        
        avg_score = sum(r["recommendation"] for r in recommendations) / len(recommendations) if recommendations else 0
        
        return "accept", f"Found {len(viable)} viable events, avg score {avg_score:.2f}"
    
    def score_and_rank(self,
                      events: List[Dict[str, Any]],
                      user_profile: Dict[str, Any],
                      cycle_count: int = 0) -> Dict[str, Any]:
        """
        Complete scoring and ranking pipeline.
        
        Args:
            events: Events to score
            user_profile: User preferences
            cycle_count: Current cycle number
            
        Returns:
            Dictionary with top10, decision, and stats
        """
        # Pre-filter
        filtered = self.pre_filter_events(events, user_profile)
        
        if not filtered:
            return {
                "top10": [],
                "decision": {"action": "revise", "notes": "No events passed access filtering"},
                "stats": {"total_events": len(events), "filtered": 0},
                "cost": 0
            }
        
        # Build prompt
        prompt = self.build_scoring_prompt(filtered, user_profile)
        
        # Call LLM for scoring
        print(f"Calling {self.model} for scoring {len(filtered)} events...")
        llm_result = self.call_llm(prompt)
        
        # Merge scores with events
        recommendations = self.merge_scores_with_events(filtered, llm_result.get("scores", []))
        
        # Sort by score
        recommendations.sort(key=lambda x: x["recommendation"], reverse=True)
        
        # Get top 10
        top10 = recommendations[:10]
        
        # Make gate decision
        decision, notes = self.make_gate_decision(recommendations, cycle_count)
        
        # Calculate stats
        stats = {
            "total_events": len(events),
            "filtered_events": len(filtered),
            "scored_events": len(recommendations),
            "viable_events": len([r for r in recommendations if r["recommendation"] >= 0.3]),
            "token_usage": llm_result.get("usage", {}),
            "api_cost": llm_result.get("cost", 0)
        }
        
        return {
            "top10": top10,
            "decision": {"action": decision, "notes": notes},
            "stats": stats,
            "cost": llm_result.get("cost", 0)
        }

# Test function
def test_publisher():
    """Test the LLM-based Recommender."""
    print("Testing LLM-based Recommender Agent")
    print("=" * 50)
    
    # Test data
    test_events = [
        {
            "title": "Climate Protest at Bryant Park",
            "summary": "Major protest against climate change policies",
            "location": "Bryant Park, NYC",
            "access_req": "open to all",
            "time": "2025-04-05",
            "url": "https://example.com/climate-protest"
        },
        {
            "title": "Met Gala 2025",
            "summary": "Exclusive fashion event at the Metropolitan Museum",
            "location": "Metropolitan Museum, NYC",
            "access_req": "press card required",
            "time": "2025-05-01",
            "url": "https://example.com/met-gala"
        },
        {
            "title": "Mayor's Town Hall",
            "summary": "Public Q&A session with NYC Mayor",
            "location": "City Hall, NYC",
            "access_req": "open to public",
            "time": "2025-03-20",
            "url": "https://example.com/town-hall"
        }
    ]
    
    test_profile = {
        "interest_areas": ["protests", "cultural events", "political"],
        "keywords": ["climate", "fashion", "activism", "protest", "government"],
        "credentials": ["press_card"],
        "location_preference": "NYC"
    }
    
    # Initialize agent
    agent = PublisherAgent()
    
    print("\nTest Events:")
    for i, event in enumerate(test_events, 1):
        print(f"  {i}. {event['title']}")
    
    print(f"\nUser Profile:")
    print(f"  Interests: {test_profile['interest_areas']}")
    print(f"  Credentials: {test_profile['credentials']}")
    
    print("\n" + "="*50)
    print("READY TO CALL OPENAI API")
    print(f"Model: {agent.model}")
    print(f"Estimated cost: ~$0.001")
    print("="*50)
    
    input("\nPress Enter to proceed with LLM scoring or Ctrl+C to cancel...")
    
    # Run scoring
    result = agent.score_and_rank(test_events, test_profile, cycle_count=0)
    
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(result["top10"], 1):
        print(f"\n{i}. {rec['title']}")
        print(f"   Score: {rec['recommendation']:.2f}")
        print(f"   Rationale: {rec['rationale']}")
    
    print(f"\nGate Decision: {result['decision']['action']}")
    print(f"Notes: {result['decision']['notes']}")
    
    print(f"\nStats:")
    for key, value in result["stats"].items():
        if key != "token_usage":
            print(f"  {key}: {value}")
    
    print(f"\nAPI Cost: ${result['cost']:.6f}")
    print(f"Results saved in: {agent.results_dir}")

if __name__ == "__main__":
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        test_publisher()
    else:
        print("Please set OPENAI_API_KEY in .env file to test the Recommender")