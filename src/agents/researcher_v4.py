"""Researcher Agent v0.4.0 - LLM-based event lead generator."""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.agents.base_agent import CachedAgent
from src.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class ResearcherV4(CachedAgent):
    """Researcher that uses LLM to generate specific event leads."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize Researcher v0.4.0.
        
        Args:
            use_cache: Whether to use caching
        """
        super().__init__(name="researcher_v4", use_cache=use_cache)
        self.llm_client = get_llm_client(model="gpt-4.1-mini", temperature=1.0)
    
    def _build_system_prompt(self, profile: Dict[str, Any]) -> str:
        """Build system prompt from user profile.
        
        Args:
            profile: User profile with preferences
            
        Returns:
            System prompt string
        """
        interests = profile.get("interests", ["news", "events"])
        location = profile.get("location", "New York City")
        
        return f"""You are an expert event researcher for photojournalists in {location}.
        
Your job is to generate SPECIFIC, CONCRETE event leads that photographers can cover.
Focus on: {', '.join(interests)}

Event Types to Consider:
- Protests and demonstrations (specific causes, organizations)
- Cultural festivals and parades (specific communities, dates)
- Political rallies and town halls (specific candidates, issues)
- Sports events and marathons (specific teams, races)
- Art exhibitions and gallery openings (specific artists, venues)
- Community events and fundraisers (specific causes, organizations)
- Press conferences and announcements (specific topics, officials)
- Street fairs and markets (specific neighborhoods, themes)

CRITICAL REQUIREMENTS:
1. Each event must be SPECIFIC and SEARCHABLE
2. Include organization names, venue names, or specific themes
3. Think about what events are LIKELY happening this week
4. Consider seasonal events, recurring events, and current news
5. Generate diverse event types for comprehensive coverage

DO NOT generate:
- Generic descriptions like "art exhibition" without specifics
- Events without searchable keywords
- Past events or unlikely future events"""
    
    def _build_user_prompt(self, location: str, time_frame: str) -> str:
        """Build user prompt for event generation.
        
        Args:
            location: Event location
            time_frame: Time frame for events
            
        Returns:
            User prompt string
        """
        # Calculate date context
        today = datetime.now()
        week_end = today + timedelta(days=7)
        two_weeks_end = today + timedelta(days=14)
        
        # Get season for context
        month = today.month
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:
            season = "Fall"
        
        # Build specific date constraints based on time_frame
        date_constraint = ""
        if "week" in time_frame.lower():
            if "this week" in time_frame.lower():
                date_constraint = f"ONLY events happening between NOW ({today.strftime('%B %d')}) and {week_end.strftime('%B %d, %Y')}"
            elif "next 2 weeks" in time_frame.lower() or "two weeks" in time_frame.lower():
                date_constraint = f"ONLY events happening between NOW ({today.strftime('%B %d')}) and {two_weeks_end.strftime('%B %d, %Y')}"
            else:
                date_constraint = f"ONLY events happening in the timeframe: {time_frame}"
        else:
            date_constraint = f"ONLY events happening in: {time_frame}"
        
        return f"""Generate 25 specific event leads for {location} {time_frame}.
        
CRITICAL DATE CONTEXT:
- Today is {today.strftime('%A, %B %d, %Y')}
- Current season: {season}
- {date_constraint}

IMPORTANT RULES:
1. DO NOT generate events that already happened (before {today.strftime('%B %d, %Y')})
2. DO NOT generate events far in the future (beyond the specified timeframe)
3. ONLY generate events realistically happening in the exact timeframe requested
4. Consider recurring events (weekly markets, regular protests, scheduled meetings)
5. Consider seasonal events appropriate for {season}

For each event, provide:
1. A specific, searchable description (organization names, venues, themes)
2. Event type category
3. Keywords for searching

Format as JSON list with structure:
{{
    "events": [
        {{
            "description": "Climate protest by Extinction Rebellion at Wall Street",
            "type": "protest",
            "keywords": ["Extinction Rebellion", "climate protest", "Wall Street"]
        }}
    ]
}}

Generate 25 diverse, specific events that photographers would want to cover."""
    
    def _build_search_query(self, event: Dict[str, Any]) -> str:
        """Build optimized search query for Tavily.
        
        Args:
            event: Event lead data
            
        Returns:
            Search query string
        """
        # Combine description with key terms
        query_parts = [event["description"]]
        
        # Add top keywords
        keywords = event.get("keywords", [])[:3]
        if keywords:
            query_parts.extend(keywords)
        
        # Add NYC context
        query_parts.append("New York City")
        
        # Add time context
        query_parts.append("2025")
        
        return " ".join(query_parts)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate event leads using LLM.
        
        Args:
            state: Workflow state with profile and search parameters
            
        Returns:
            Updated state with event leads
        """
        try:
            # Extract parameters
            profile = state.get("profile", {})
            location = state.get("location", "New York City")
            time_frame = state.get("time_frame", "this week")
            
            # Check cache
            cache_key = f"{location}_{time_frame}"
            cached_result = self.get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached leads for {cache_key}")
                state["leads"] = cached_result["leads"]
                state["researcher_metrics"] = cached_result["metrics"]
                return state
            
            # Build prompts
            system_prompt = self._build_system_prompt(profile)
            user_prompt = self._build_user_prompt(location, time_frame)
            
            # Generate leads with LLM
            logger.info("Generating event leads with LLM...")
            response = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                schema={
                    "type": "object",
                    "required": ["events"],
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["description", "type", "keywords"],
                                "properties": {
                                    "description": {"type": "string"},
                                    "type": {"type": "string"},
                                    "keywords": {"type": "array"}
                                }
                            }
                        }
                    }
                }
            )
            
            # Process leads
            events = response["parsed_content"]["events"]
            leads = []
            
            for event in events:
                lead = {
                    "description": event["description"],
                    "type": event["type"],
                    "keywords": event["keywords"],
                    "search_query": self._build_search_query(event)
                }
                leads.append(lead)
            
            # Track metrics
            metrics = {
                "total_leads": len(leads),
                "llm_cost": response["cost"],
                "llm_tokens": response["total_tokens"],
                "generation_time": response["elapsed_time"]
            }
            
            # Update cost tracking
            self.total_cost += response["cost"]
            
            # Save to cache
            result = {"leads": leads, "metrics": metrics}
            self.save_to_cache(cache_key, result)
            
            # Update state
            state["leads"] = leads
            state["researcher_metrics"] = metrics
            
            logger.info(
                f"Generated {len(leads)} event leads, "
                f"cost: ${response['cost']:.4f}, "
                f"time: {response['elapsed_time']:.2f}s"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating leads: {e}")
            self.errors.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "state": state
            })
            
            # Return empty leads on error
            state["leads"] = []
            state["researcher_metrics"] = {"error": str(e)}
            return state
    
    def validate_output(self, state: Dict[str, Any]) -> bool:
        """Validate researcher output.
        
        Args:
            state: State with leads
            
        Returns:
            True if valid
        """
        if "leads" not in state:
            logger.error("No leads in state")
            return False
        
        leads = state["leads"]
        if not leads:
            logger.warning("No leads generated")
            return True  # Empty is valid but not ideal
        
        # Check required fields
        for lead in leads:
            if not all(key in lead for key in ["description", "type", "keywords", "search_query"]):
                logger.error(f"Lead missing required fields: {lead}")
                return False
        
        logger.info(f"Validated {len(leads)} leads")
        return True