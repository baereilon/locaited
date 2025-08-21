"""Researcher Agent - LLM-based event lead generator."""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from locaited.agents.base_agent import CachedAgent
from locaited.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class ResearcherAgent(CachedAgent):
    """Researcher that uses LLM to generate specific event leads."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize Researcher agent.
        
        Args:
            use_cache: Whether to use caching
        """
        super().__init__(name="researcher", use_cache=use_cache)
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
        
Your job is to generate REAL, VERIFIABLE event leads that photographers can cover.
Focus on: {', '.join(interests)}

STRATEGY FOR FINDING REAL EVENTS:
1. Think about ESTABLISHED, RECURRING events in {location}:
   - Weekly farmers markets (Union Square, Brooklyn, etc.)
   - Regular museum events (First Saturdays, Free Fridays)
   - Scheduled sports games (Knicks, Nets, Rangers, Yankees)
   - Known annual events happening this time of year

2. Consider VERIFIED VENUE SCHEDULES:
   - Madison Square Garden events
   - Lincoln Center performances
   - Brooklyn Academy of Music shows
   - Museum exhibitions with specific programming
   - City Hall press conferences

3. Think about PREDICTABLE EVENTS:
   - Community Board meetings (monthly)
   - Protest movements with regular actions
   - Religious celebrations for this season
   - School and university events

4. Consider CURRENT NEWS CONTEXT:
   - Ongoing political campaigns
   - Recent news that might trigger protests
   - Seasonal activities for {location}

CRITICAL ANTI-HALLUCINATION RULES:
1. Only suggest events from KNOWN VENUES and ESTABLISHED ORGANIZATIONS
2. Focus on RECURRING events that definitely happen
3. Use REAL organization names, not made-up ones
4. Consider what ACTUALLY happens in {location} during this time
5. Generate MANY leads (we'll verify them later)

DO NOT:
- Make up organization names
- Invent events that sound plausible but don't exist
- Create fake venues or locations"""
    
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
            "description": "Union Square Greenmarket farmers market",
            "type": "market",
            "keywords": ["Union Square", "Greenmarket", "farmers market"],
            "confidence": "high",
            "source_hint": "Weekly recurring event"
        }}
    ]
}}

Generate 50 diverse events that photographers would want to cover. Focus on REAL, RECURRING, VERIFIABLE events."""
    
    def _verify_event_reality(self, events: List[Dict], location: str, time_frame: str) -> Dict[str, Any]:
        """Verify if events are real or hallucinated using dedicated LLM check.
        
        Args:
            events: List of events to verify
            location: Event location
            time_frame: Time frame
            
        Returns:
            Dict with verified and rejected events
        """
        if not events:
            return {"verified": [], "rejected": []}
            
        system_prompt = f"""You are a fact-checker verifying if events in {location} are REAL or HALLUCINATED.

Your job is to determine if each event is:
1. REAL - Known venue, established organization, recurring event, or verifiable
2. SUSPICIOUS - Might exist but unclear, needs more verification
3. HALLUCINATED - Made up, doesn't exist, fake organization/venue

Consider:
- Is this a REAL venue/organization that exists in {location}?
- Is this type of event ACTUALLY held at this venue?
- Is this a known recurring event?
- Does the organization actually exist and do these types of events?
- Is the timing realistic for this type of event?

BE VERY STRICT - if you're not sure it's real, mark it as suspicious or hallucinated."""

        verified_events = []
        rejected_events = []
        
        # Process in batches of 10 to avoid token limits
        for i in range(0, len(events), 10):
            batch = events[i:i+10]
            
            user_prompt = f"""Verify if these events are REAL or HALLUCINATED:

{json.dumps(batch, indent=2)}

For each event, determine:
1. Is the venue/location real? (Google it mentally)
2. Is the organization real? (Does it actually exist?)
3. Is this type of event realistic for this venue/org?
4. Would this event actually happen during {time_frame}?

Return JSON:
{{
    "verifications": [
        {{
            "event_description": "...",
            "status": "REAL" or "SUSPICIOUS" or "HALLUCINATED",
            "confidence": 0-100,
            "reason": "Why you think it's real or fake",
            "suggested_search": "Better search query if needed"
        }}
    ]
}}"""
            
            try:
                response = self.llm_client.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=1500,
                    schema={
                        "type": "object",
                        "required": ["verifications"],
                        "properties": {
                            "verifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["event_description", "status", "confidence", "reason"],
                                    "properties": {
                                        "event_description": {"type": "string"},
                                        "status": {"type": "string", "enum": ["REAL", "SUSPICIOUS", "HALLUCINATED"]},
                                        "confidence": {"type": "integer"},
                                        "reason": {"type": "string"},
                                        "suggested_search": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
                
                verifications = response["parsed_content"]["verifications"]
                
                # Match verifications back to original events
                for j, verification in enumerate(verifications):
                    if j < len(batch):
                        original_event = batch[j]
                        if verification["status"] == "REAL" and verification["confidence"] >= 70:
                            original_event["verification_status"] = "verified"
                            original_event["confidence_score"] = verification["confidence"]
                            verified_events.append(original_event)
                        elif verification["status"] == "SUSPICIOUS" and verification["confidence"] >= 50:
                            # Give suspicious events a chance with modified search
                            original_event["verification_status"] = "needs_verification"
                            original_event["confidence_score"] = verification["confidence"]
                            if verification.get("suggested_search"):
                                original_event["search_query"] = verification["suggested_search"]
                            verified_events.append(original_event)
                        else:
                            original_event["rejection_reason"] = verification["reason"]
                            rejected_events.append(original_event)
                
                logger.info(f"Verified batch: {len([v for v in verifications if v['status'] == 'REAL'])} real, "
                          f"{len([v for v in verifications if v['status'] == 'SUSPICIOUS'])} suspicious, "
                          f"{len([v for v in verifications if v['status'] == 'HALLUCINATED'])} hallucinated")
                
            except Exception as e:
                logger.error(f"Verification failed for batch: {e}")
                # If verification fails, be conservative and reject the batch
                rejected_events.extend(batch)
        
        return {
            "verified": verified_events,
            "rejected": rejected_events,
            "verification_stats": {
                "total_checked": len(events),
                "verified": len(verified_events),
                "rejected": len(rejected_events)
            }
        }
    
    def _expand_generic_events(self, generic_events: List[Dict], location: str, date_range: tuple) -> List[Dict]:
        """Expand generic events into specific, photographable sub-events.
        
        Args:
            generic_events: List of generic events that need expansion
            location: Event location
            date_range: Tuple of (start_date, end_date)
            
        Returns:
            List of specific sub-events
        """
        if not generic_events:
            return []
            
        start_date, end_date = date_range
        all_expanded = []
        
        # Process in batches of 3 to avoid JSON parsing issues (reduced from 5 to prevent truncation)
        batch_size = 3
        total_batches = (len(generic_events) + batch_size - 1) // batch_size
        
        for i in range(0, len(generic_events), batch_size):
            batch_num = (i // batch_size) + 1
            batch = generic_events[i:i+batch_size]
            logger.info(f"RESEARCHER PROGRESS: Expanding batch {batch_num}/{total_batches} ({len(batch)} generic events)...")
            
            expanded_batch = self._expand_generic_batch(batch, location, start_date, end_date)
            all_expanded.extend(expanded_batch)
            
            if expanded_batch:
                logger.info(f"Batch {batch_num} expanded into {len(expanded_batch)} specific events")
            
        return all_expanded
    
    def _expand_generic_batch(self, generic_events: List[Dict], location: str, start_date, end_date) -> List[Dict]:
        """Expand a batch of generic events."""
        if not generic_events:
            return []
        
        system_prompt = f"""You are an expert at finding specific, photographable events within larger festivals and ongoing events.

Your job is to take generic events (like "Fashion Week" or "Art Fair") and find SPECIFIC sub-events that photographers can cover.

For each generic event, find:
1. Opening ceremonies or launch events
2. Specific shows, performances, or demonstrations
3. Celebrity appearances or special guests
4. Public events or street activities
5. Behind-the-scenes opportunities
6. Closing events or award ceremonies

Requirements:
- Each sub-event MUST have a specific date between {start_date.strftime('%B %d')} and {end_date.strftime('%B %d, %Y')}
- Each sub-event MUST have a specific time and venue
- Focus on visually interesting moments with action and emotion
- Include diverse perspectives (main events, street style, protests, parties)"""

        user_prompt = f"""These generic events were found for {location}. Find SPECIFIC sub-events within them:

{json.dumps(generic_events, indent=2)}

For each generic event, find 2-3 specific, photographable moments happening between {start_date.strftime('%B %d')} and {end_date.strftime('%B %d, %Y')}.

Examples:
- If "Fashion Week" → "Marc Jacobs runway show at Spring Studios, Feb 1, 7PM" or "Street style photography outside Lincoln Center, Feb 2, all day"
- If "Food Festival" → "Chef competition finals at Brooklyn Expo Center, Jan 28, 3PM" or "Opening ceremony with mayor at Grand Army Plaza, Jan 27, 11AM"
- If "Art Fair" → "VIP preview night at Javits Center, Jan 30, 6PM" or "Live mural painting demo by KAWS, Jan 31, 2PM"

Format as JSON:
{{
    "expanded_events": [
        {{
            "parent_event": "Fashion Week",
            "description": "Opening runway show by Designer X at Venue Y",
            "type": "fashion_show",
            "keywords": ["designer name", "venue", "fashion week"],
            "date": "February 1, 2025",
            "time": "7:00 PM",
            "venue": "Spring Studios, 50 Varick St",
            "photo_opportunity": "Models, celebrities, runway action"
        }}
    ]
}}"""

        try:
            response = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1200,  # Reduced to prevent truncation for 3 events × 3 sub-events each
                schema={
                    "type": "object",
                    "required": ["expanded_events"],
                    "properties": {
                        "expanded_events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["description", "type", "keywords", "date", "venue"],
                                "properties": {
                                    "parent_event": {"type": "string"},
                                    "description": {"type": "string"},
                                    "type": {"type": "string"},
                                    "keywords": {"type": "array"},
                                    "date": {"type": "string"},
                                    "time": {"type": "string"},
                                    "venue": {"type": "string"},
                                    "photo_opportunity": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            )
            
            expanded = response["parsed_content"]["expanded_events"]
            
            # Add search queries to expanded events
            for event in expanded:
                event["search_query"] = self._build_search_query(event)
                event["is_expanded"] = True  # Mark as expanded from generic
                
            logger.info(f"Expanded {len(generic_events)} generic events into {len(expanded)} specific sub-events")
            return expanded
            
        except Exception as e:
            logger.error(f"Failed to expand generic events: {e}")
            return []
    
    def _analyze_validation_failures(self, validation_notes: List[str], removed_count: int) -> Dict[str, Any]:
        """Analyze why events failed validation to improve next generation.
        
        Args:
            validation_notes: Notes from validation process
            removed_count: Number of events removed
            
        Returns:
            Analysis dict with failure patterns and suggestions
        """
        # Common failure patterns
        patterns = {
            "date_issues": ["outside date range", "no specific date", "already happened", "too far future"],
            "specificity_issues": ["too generic", "no specific", "vague", "broad"],
            "verification_issues": ["no source", "can't verify", "no URL", "fake"],
            "relevance_issues": ["not newsworthy", "not photographic", "not interesting"]
        }
        
        analysis = {
            "main_issues": [],
            "suggestions": []
        }
        
        # Analyze validation notes
        notes_text = " ".join(validation_notes).lower()
        
        for category, keywords in patterns.items():
            if any(keyword in notes_text for keyword in keywords):
                analysis["main_issues"].append(category)
                
        # Generate improvement suggestions based on issues
        if "date_issues" in analysis["main_issues"]:
            analysis["suggestions"].append("Focus on events happening THIS WEEK with specific dates")
        if "specificity_issues" in analysis["main_issues"]:
            analysis["suggestions"].append("Include venue names, organization names, and specific event titles")
        if "verification_issues" in analysis["main_issues"]:
            analysis["suggestions"].append("Focus on established events from known organizations")
        if "relevance_issues" in analysis["main_issues"]:
            analysis["suggestions"].append("Prioritize visually interesting events with action and emotion")
            
        return analysis
    
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
    
    def _build_adjusted_system_prompt(self, profile: Dict[str, Any]) -> str:
        """Build more flexible system prompt for retry attempts.
        
        Args:
            profile: User profile with preferences
            
        Returns:
            Adjusted system prompt string
        """
        interests = profile.get("interests", ["news", "events"])
        location = profile.get("location", "New York City")
        
        return f"""You are an expert event researcher for photojournalists in {location}.

Your job is to generate LIKELY, PLAUSIBLE event leads that photographers can cover.
Focus on: {', '.join(interests)}

ADJUSTED APPROACH - Be more inclusive:
- Generate events that are LIKELY to happen even if not 100% confirmed
- Include recurring events (weekly markets, regular meetings, ongoing exhibitions)
- Consider seasonal activities and typical events for this time period
- Think about what photographers would WANT to cover
- Include both confirmed and likely events

Event Types to Consider:
- Public events and gatherings (community events, markets, festivals)
- Cultural activities (art shows, performances, exhibitions)
- Recurring activities (weekly protests, regular meetings, ongoing shows)
- Seasonal events appropriate for current time period
- Newsworthy activities that photographers cover

REQUIREMENTS:
1. Events should be searchable and specific enough to verify
2. Include organization names, venue names, or specific themes when possible
3. Consider what's typically happening during this season/timeframe
4. Generate diverse event types for comprehensive coverage

BE MORE GENEROUS - include events that seem plausible and photographically interesting."""
    
    def _build_adjusted_user_prompt(self, location: str, time_frame: str) -> str:
        """Build more flexible user prompt for retry attempts.
        
        Args:
            location: Event location
            time_frame: Time frame for events
            
        Returns:
            Adjusted user prompt string
        """
        today = datetime.now()
        
        return f"""Generate 15 PLAUSIBLE event leads for {location} {time_frame}.

ADJUSTED STRATEGY - Cast a wider net:
- Include both confirmed events AND likely recurring events
- Consider what typically happens during this time period
- Think about ongoing exhibitions, regular markets, weekly meetings
- Include events that photographers would want to cover

Today is {today.strftime('%A, %B %d, %Y')}

For each event, provide:
1. A realistic, searchable description
2. Event type category  
3. Keywords for searching

Focus on PHOTOGRAPHIC POTENTIAL and LIKELIHOOD rather than perfect confirmation.

Format as JSON list with structure:
{{
    "events": [
        {{
            "description": "Weekly Union Square Greenmarket farmers market",
            "type": "market",
            "keywords": ["Union Square", "Greenmarket", "farmers market"]
        }}
    ]
}}

Generate 15 diverse, PLAUSIBLE events."""
    
    def _build_feedback_informed_prompt(self, location: str, time_frame: str, profile: Dict[str, Any], feedback: Dict[str, Any]) -> tuple:
        """Build prompts informed by validation feedback.
        
        Args:
            location: Event location
            time_frame: Time frame for events
            profile: User profile
            feedback: Analysis of what went wrong
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        today = datetime.now()
        end_date = today + timedelta(days=7) if "week" in time_frame.lower() else today + timedelta(days=14)
        interests = profile.get("interests", ["news", "events"])
        
        system_prompt = f"""You are an expert event researcher for photojournalists in {location}.

CRITICAL LEARNING FROM PREVIOUS ATTEMPTS:
{' | '.join(feedback.get('suggestions', []))}

Focus on events that match these user interests: {', '.join(interests)}

IMPROVED STRATEGY:
1. ONLY suggest events between {today.strftime('%B %d')} and {end_date.strftime('%B %d, %Y')}
2. Be SPECIFIC: Include venue names, organization names, performer names
3. Avoid generic events - each must be a discrete, photographable moment
4. Think about what's ACTUALLY happening this specific week
5. Consider: protests with specific causes, markets at specific locations, 
   shows with named performers, openings with specific galleries

Examples of GOOD events:
- "Brooklyn Museum First Saturday community celebration on February 1"
- "Extinction Rebellion climate protest at Wall Street on January 28, 2PM"
- "Smorgasburg Winter Market opening day at Brooklyn Bridge Park, January 25"

Examples of BAD events (DO NOT GENERATE):
- "Fashion Week" (too generic, not specific)
- "Art exhibition" (ongoing, not discrete event)
- "Food festival" (no specific date/location)"""
        
        user_prompt = f"""Generate 20 SPECIFIC, VERIFIABLE events for {location} happening between {today.strftime('%B %d, %Y')} and {end_date.strftime('%B %d, %Y')}.

REQUIREMENTS:
1. Each event MUST have a specific date within the range
2. Each event MUST have a specific venue or location  
3. Each event MUST be a discrete, time-bound occurrence
4. Focus on: {', '.join(interests)}

Today is {today.strftime('%A, %B %d, %Y')}

Format as JSON:
{{
    "events": [
        {{
            "description": "Specific event with venue and organization",
            "type": "event_type",
            "keywords": ["specific", "searchable", "terms"],
            "expected_date": "January 25, 2025",
            "venue": "Specific location name"
        }}
    ]
}}"""
        
        return system_prompt, user_prompt
    
    def _validate_and_enhance_leads(self, initial_events: List[Dict], location: str, time_frame: str, profile: Dict[str, Any], max_iterations: int = 10, lenient: bool = False) -> Dict[str, Any]:
        """Iteratively validate and enhance leads with dates and URLs.
        
        Args:
            initial_events: Initial event leads to validate
            location: Event location
            time_frame: Time frame for events
            profile: User profile with interests
            max_iterations: Maximum LLM calls for validation
            lenient: Whether to use lenient validation mode
            
        Returns:
            Dict with validated events and metrics
        """
        today = datetime.now()
        interests = profile.get("interests", ["news", "events"])
        
        # Calculate exact date range
        end_date = today
        if "week" in time_frame.lower():
            if "this week" in time_frame.lower():
                end_date = today + timedelta(days=7)
            elif "next 2 weeks" in time_frame.lower() or "two weeks" in time_frame.lower():
                end_date = today + timedelta(days=14)
            else:
                end_date = today + timedelta(days=7)
        else:
            end_date = today + timedelta(days=7)
        
        # Adjust validation strictness based on lenient mode
        if lenient:
            validation_prompt = f"""You are a fact-checker validating event leads for photojournalists.

LENIENT VALIDATION MODE - Be accepting but categorize smartly:

DATE REQUIREMENTS:
- Events MUST be between {today.strftime('%B %d, %Y')} and {end_date.strftime('%B %d, %Y')}
- Accept approximate dates if within range

CATEGORIZE events into three groups:

1. VALIDATED EVENTS (directly usable):
   - Have dates within range (even if approximate)
   - Have specific venues or locations
   - Are discrete, photographable moments
   - Have some evidence or seem plausible

2. GENERIC EVENTS (need expansion - USE SPARINGLY):
   - ONLY truly broad umbrella events (e.g., "Fashion Week" without specific shows)
   - ONLY vague festivals without any specific activities
   - DO NOT mark as generic if it's a specific recurring event
   - Most events should be VALIDATED, not generic

3. REJECTED EVENTS (remove):
   - Outside the date range completely
   - Too vague even for expansion
   - Don't align with user interests: {', '.join(interests)}

For VALIDATED events, provide enhanced details.
For GENERIC events, note why they're generic and what expansion potential they have.

BE LENIENT BUT SMART - generic events aren't failures, they're opportunities to find specifics!"""
        else:
            validation_prompt = f"""You are an expert fact-checker validating event leads for photojournalists.

STRICT VALIDATION MODE WITH SMART FILTERING:

DATE REQUIREMENTS (ABSOLUTELY CRITICAL):
- Events MUST be between {today.strftime('%B %d, %Y')} and {end_date.strftime('%B %d, %Y')}
- REJECT any events outside this exact date range
- Require specific dates (January 25, 2025) not vague timeframes

CATEGORIZATION FOR EXPANSION:
- MARK AS GENERIC: Any event that could have multiple photo opportunities within it
- MARK AS GENERIC: Recurring venues/events (museums, markets, sports venues)
- MARK AS GENERIC: Multi-day festivals or events
- MARK AS GENERIC: Any venue with regular programming
- We WANT to expand these to find ALL possible photo opportunities!
- Events should align with user interests: {', '.join(interests)}

VERIFICATION REQUIREMENTS:
1. Each event MUST have a real URL source confirming it exists
2. The URL must be from a credible source (news, official org, event platform)
3. The event details must match what's in the source

For each VALID event, provide:
- Specific date and time if available
- Exact location/venue
- One reliable URL source (news site, event page, organization website)
- Updated description with precise details

STRICT RULES:
- If you cannot find a real URL for an event, REMOVE it
- If an event is too generic or vague, REMOVE it
- If an event already happened, REMOVE it
- Only keep events with strong photojournalistic value

Return events in this format:
{{
    "validated_events": [
        {{
            "description": "Specific event description with venue and organizer",
            "type": "event_type",
            "keywords": ["keyword1", "keyword2"],
            "date": "January 25, 2025",
            "time": "2:00 PM" or "All day",
            "venue": "Specific venue name and address",
            "source_url": "https://reliable-source.com/event-page",
            "verification_note": "Brief note on why this event is real and newsworthy"
        }}
    ],
    "generic_events": [
        {{
            "description": "Fashion Week NYC",
            "type": "fashion",
            "keywords": ["fashion week", "NYC", "runway"],
            "reason_generic": "Broad event that needs specific shows/dates"
        }}
    ],
    "removed_count": 5,
    "validation_notes": "Summary of validation process"
}}"""

        all_responses = []
        current_events = initial_events
        generic_events_collected = []  # Collect generic events for expansion
        total_cost = 0
        total_tokens = 0
        total_time = 0
        
        for iteration in range(max_iterations):
            if not current_events:
                logger.warning(f"No events left to validate after iteration {iteration}")
                break
                
            # Prepare batch for validation (process 5 at a time to avoid token limits)
            batch_size = min(5, len(current_events))
            batch_events = current_events[:batch_size]
            
            validation_user_prompt = f"""Validate these {batch_size} event leads for {location}:

{json.dumps(batch_events, indent=2)}

CRITICAL CONTEXT:
- Today: {today.strftime('%A, %B %d, %Y')}
- Valid date range: {today.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}
- User interests: {', '.join(interests)}

SEPARATE events into three categories:

1. VALID EVENTS - Keep these:
   - Have specific dates within range ({today.strftime('%B %d')} to {end_date.strftime('%B %d')})
   - Have specific venues and times
   - Are discrete, photographable moments
   - Can be verified with sources

2. GENERIC EVENTS - Mark for expansion (ONLY truly broad events):
   - ONLY large umbrella events like "Fashion Week" (not specific shows)
   - ONLY general festivals without specific activities mentioned
   - DO NOT mark specific events as generic just because they lack full details
   - Most events should be VALID, not generic

3. REJECTED EVENTS - Remove these:
   - Outside the date range
   - Too vague to expand
   - Don't align with user interests
   - Can't be verified at all

Return all three categories so we can expand the generic ones into specific opportunities."""

            try:
                logger.info(f"Validation iteration {iteration + 1}: Processing {batch_size} events")
                
                response = self.llm_client.complete_json(
                    system_prompt=validation_prompt,
                    user_prompt=validation_user_prompt,
                    max_tokens=2500,
                    schema={
                        "type": "object",
                        "required": ["validated_events", "generic_events", "removed_count", "validation_notes"],
                        "properties": {
                            "validated_events": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["description", "type", "keywords", "date", "source_url"],
                                    "properties": {
                                        "description": {"type": "string"},
                                        "type": {"type": "string"},
                                        "keywords": {"type": "array"},
                                        "date": {"type": "string"},
                                        "time": {"type": "string"},
                                        "venue": {"type": "string"},
                                        "source_url": {"type": "string"},
                                        "verification_note": {"type": "string"}
                                    }
                                }
                            },
                            "generic_events": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["description", "type", "keywords"],
                                    "properties": {
                                        "description": {"type": "string"},
                                        "type": {"type": "string"},
                                        "keywords": {"type": "array"},
                                        "reason_generic": {"type": "string"}
                                    }
                                }
                            },
                            "removed_count": {"type": "integer"},
                            "validation_notes": {"type": "string"}
                        }
                    }
                )
                
                all_responses.append(response)
                total_cost += response["cost"]
                total_tokens += response["total_tokens"]
                total_time += response["elapsed_time"]
                
                validated_batch = response["parsed_content"]["validated_events"]
                generic_batch = response["parsed_content"].get("generic_events", [])
                removed_count = response["parsed_content"]["removed_count"]
                
                # Collect generic events for later expansion
                if generic_batch:
                    generic_events_collected.extend(generic_batch)
                    logger.info(f"Found {len(generic_batch)} generic events to expand")
                
                logger.info(f"Iteration {iteration + 1}: Validated {len(validated_batch)}/{batch_size} events, {len(generic_batch)} generic, removed {removed_count}")
                
                # Remove processed events from current_events
                current_events = current_events[batch_size:]
                
                # If we have enough quality events, we can stop early
                total_validated = sum(len(r["parsed_content"]["validated_events"]) for r in all_responses)
                if total_validated >= 15:  # Stop if we have 15+ quality events
                    logger.info(f"Reached {total_validated} validated events, stopping early")
                    break
                    
            except Exception as e:
                logger.error(f"Validation iteration {iteration + 1} failed: {e}")
                break
        
        # Combine all validated events
        final_events = []
        total_removed = 0
        validation_notes = []
        
        for response in all_responses:
            final_events.extend(response["parsed_content"]["validated_events"])
            total_removed += response["parsed_content"]["removed_count"]
            validation_notes.append(response["parsed_content"]["validation_notes"])
        
        # Expand generic events into specific sub-events
        if generic_events_collected:
            logger.info(f"Expanding {len(generic_events_collected)} generic events into specific sub-events...")
            date_range = (today, end_date)
            expanded_events = self._expand_generic_events(generic_events_collected, location, date_range)
            
            if expanded_events:
                logger.info(f"Successfully expanded into {len(expanded_events)} specific sub-events")
                final_events.extend(expanded_events)
                
                # Update cost tracking for the expansion
                if hasattr(self.llm_client, 'last_cost'):
                    total_cost += self.llm_client.last_cost
                    total_tokens += getattr(self.llm_client, 'last_tokens', 0)
                    total_time += getattr(self.llm_client, 'last_time', 0)
        
        # Add search queries to final events
        for event in final_events:
            event["search_query"] = self._build_search_query(event)
        
        return {
            "events": final_events,
            "cost": total_cost,
            "total_tokens": total_tokens,
            "elapsed_time": total_time,
            "validation_summary": {
                "initial_count": len(initial_events),
                "final_count": len(final_events),
                "removed_count": total_removed,
                "iterations_used": len(all_responses),
                "notes": " | ".join(validation_notes)
            }
        }
    
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
            
            # Step 1: Generate MORE initial leads with LLM (50 instead of 25)
            logger.info("RESEARCHER PROGRESS: Step 1/4 - Generating 50 initial event leads...")
            initial_response = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3500,  # Increased for more events
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
                                    "keywords": {"type": "array"},
                                    "confidence": {"type": "string"},
                                    "source_hint": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            )
            
            # Step 2: First check for hallucinations
            initial_events = initial_response["parsed_content"]["events"]
            logger.info(f"RESEARCHER PROGRESS: Step 2/4 - Checking {len(initial_events)} events for hallucinations...")
            
            verification_result = self._verify_event_reality(initial_events, location, time_frame)
            verified_events = verification_result["verified"]
            logger.info(f"Verification: {len(verified_events)} real events, {len(verification_result['rejected'])} rejected as hallucinated")
            
            # Step 3: Validate and enhance only the verified events
            if verified_events:
                logger.info(f"RESEARCHER PROGRESS: Step 3/4 - Validating and enhancing {len(verified_events)} verified leads...")
                validation_result = self._validate_and_enhance_leads(verified_events, location, time_frame, profile)
                leads = validation_result["events"]
            else:
                logger.warning("No events passed hallucination check!")
                leads = []
                validation_result = {"events": [], "cost": 0, "total_tokens": 0, "elapsed_time": 0}
            
            # Step 3: If we got fewer than 5 leads, analyze failures and try again with smarter approach
            if len(leads) < 5:
                logger.warning(f"Only {len(leads)} leads passed validation, analyzing failures...")
                
                # Analyze what went wrong
                validation_notes = [validation_result.get("validation_summary", {}).get("notes", "")]
                removed_count = validation_result.get("validation_summary", {}).get("removed_count", 0)
                feedback = self._analyze_validation_failures(validation_notes, removed_count)
                
                logger.info(f"Failure analysis: {feedback}")
                
                # Try with feedback-informed prompts
                logger.info("RESEARCHER PROGRESS: Regenerating with smarter strategy based on feedback...")
                feedback_system_prompt, feedback_user_prompt = self._build_feedback_informed_prompt(
                    location, time_frame, profile, feedback
                )
                
                retry_response = self.llm_client.complete_json(
                    system_prompt=feedback_system_prompt,
                    user_prompt=feedback_user_prompt,
                    max_tokens=2500,
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
                                        "keywords": {"type": "array"},
                                        "expected_date": {"type": "string"},
                                        "venue": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
                
                retry_events = retry_response["parsed_content"]["events"]
                
                # Validate with lenient mode first
                retry_validation = self._validate_and_enhance_leads(
                    retry_events, location, time_frame, profile, max_iterations=5, lenient=True
                )
                
                # Combine leads from both attempts
                leads.extend(retry_validation["events"])
                
                # Remove duplicates based on description similarity
                unique_leads = []
                seen_descriptions = set()
                for lead in leads:
                    desc_key = lead["description"].lower()[:50]  # Use first 50 chars as key
                    if desc_key not in seen_descriptions:
                        unique_leads.append(lead)
                        seen_descriptions.add(desc_key)
                leads = unique_leads[:15]  # Keep top 15 unique leads
                
                # Update combined costs
                total_cost = initial_response["cost"] + validation_result["cost"] + retry_response["cost"] + retry_validation["cost"]
                total_tokens = initial_response["total_tokens"] + validation_result["total_tokens"] + retry_response["total_tokens"] + retry_validation["total_tokens"]
                total_time = initial_response["elapsed_time"] + validation_result["elapsed_time"] + retry_response["elapsed_time"] + retry_validation["elapsed_time"]
                
                # If still too few, try one more time with very lenient approach
                if len(leads) < 3:
                    logger.warning("Still insufficient leads, final attempt with adjusted criteria...")
                    adjusted_system_prompt = self._build_adjusted_system_prompt(profile)
                    adjusted_user_prompt = self._build_adjusted_user_prompt(location, time_frame)
                    
                    final_response = self.llm_client.complete_json(
                        system_prompt=adjusted_system_prompt,
                        user_prompt=adjusted_user_prompt,
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
                    
                    final_events = final_response["parsed_content"]["events"]
                    final_validation = self._validate_and_enhance_leads(
                        final_events, location, time_frame, profile, max_iterations=3, lenient=True
                    )
                    leads.extend(final_validation["events"])
                    
                    # Update combined costs
                    total_cost += final_response["cost"] + final_validation["cost"]
                    total_tokens += final_response["total_tokens"] + final_validation["total_tokens"]
                    total_time += final_response["elapsed_time"] + final_validation["elapsed_time"]
            
            # Combine metrics from all phases (if no retries, this is the original calculation)
            if 'total_cost' not in locals():
                total_cost = initial_response["cost"] + validation_result["cost"]
                total_tokens = initial_response["total_tokens"] + validation_result["total_tokens"]
                total_time = initial_response["elapsed_time"] + validation_result["elapsed_time"]
            
            # Track comprehensive metrics
            metrics = {
                "total_leads": len(leads),
                "llm_cost": total_cost,
                "llm_tokens": total_tokens,
                "generation_time": total_time,
                "validation_summary": validation_result["validation_summary"],
                "phase_breakdown": {
                    "initial_generation": {
                        "cost": initial_response["cost"],
                        "tokens": initial_response["total_tokens"],
                        "time": initial_response["elapsed_time"],
                        "events_generated": len(initial_events)
                    },
                    "validation_enhancement": {
                        "cost": validation_result["cost"],
                        "tokens": validation_result["total_tokens"],
                        "time": validation_result["elapsed_time"],
                        "events_validated": len(leads),
                        "iterations_used": validation_result["validation_summary"]["iterations_used"]
                    }
                }
            }
            
            # Update cost tracking
            self.total_cost += total_cost
            
            # Save to cache
            result = {"leads": leads, "metrics": metrics}
            self.save_to_cache(cache_key, result)
            
            # Update state
            state["leads"] = leads
            state["researcher_metrics"] = metrics
            
            logger.info(
                f"Generated {len(leads)} event leads, "
                f"cost: ${total_cost:.4f}, "
                f"time: {total_time:.2f}s"
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
        required_fields = ["description", "type", "keywords", "search_query"]
        for lead in leads:
            if not all(key in lead for key in required_fields):
                logger.error(f"Lead missing required fields: {lead}")
                return False
            
            # Check if validated leads have additional required fields
            if "source_url" in lead and "date" in lead:
                if not lead.get("source_url") or not lead.get("date"):
                    logger.error(f"Validated lead missing URL or date: {lead}")
                    return False
        
        logger.info(f"Validated {len(leads)} leads")
        return True