"""Publisher Agent - Event extraction and gate decision."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from locaited.agents.base_agent import CachedAgent
from locaited.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class PublisherAgent(CachedAgent):
    """Publisher that extracts events and makes gate decisions."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize Publisher v0.4.0.
        
        Args:
            use_cache: Whether to use caching
        """
        super().__init__(name="publisher", use_cache=use_cache)
        self.llm_client = get_llm_client(model="gpt-4.1-mini", temperature=1.0)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence to extract events and make gate decision.
        
        Args:
            state: Workflow state with evidence from Fact-Checker
            
        Returns:
            Updated state with events or feedback
        """
        try:
            # Extract evidence
            evidence = state.get("evidence", [])
            if not evidence:
                logger.warning("No evidence to process")
                state["events"] = []
                state["gate_decision"] = "RETRY"
                state["feedback"] = "No evidence found. Need to generate different event leads."
                return state
            
            # Extract context for gate decision
            profile = state.get("profile", {})
            leads = state.get("leads", [])
            
            # Process evidence with LLM
            logger.info(f"Processing {len(evidence)} evidence items...")
            unique_events = self._process_evidence_with_llm(evidence)
            
            # Make gate decision
            logger.info(f"Making gate decision on {len(unique_events)} unique events...")
            gate_result = self._make_gate_decision(
                events=unique_events,
                profile=profile,
                leads=leads
            )
            
            # Update state based on gate decision
            if gate_result["decision"] == "APPROVE":
                # Format and return top events
                final_events = self._format_final_output(gate_result["events"])
                
                state["events"] = final_events
                state["gate_decision"] = "APPROVE"
                state["publisher_metrics"] = {
                    "unique_events_found": len(unique_events),
                    "events_approved": len(final_events),
                    "llm_cost": self.total_cost
                }
                
                logger.info(f"Approved {len(final_events)} events for publication")
                
            else:  # RETRY
                state["events"] = []
                state["gate_decision"] = "RETRY"
                state["feedback"] = gate_result["feedback"]
                state["publisher_metrics"] = {
                    "unique_events_found": len(unique_events),
                    "events_approved": 0,
                    "retry_reason": gate_result["feedback"]
                }
                
                logger.info(f"Requesting retry: {gate_result['feedback']}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error processing evidence: {e}")
            self.errors.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            
            state["events"] = []
            state["gate_decision"] = "ERROR"
            state["publisher_metrics"] = {"error": str(e)}
            return state
    
    def _process_evidence_with_llm(self, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and deduplicate events from evidence using LLM.
        
        Args:
            evidence: List of evidence items from Fact-Checker
            
        Returns:
            List of unique events
        """
        # Build prompt for extraction
        system_prompt = """You are an expert at extracting specific event information from search results.

Your job is to:
1. Extract concrete events with specific dates (YYYY-MM-DD format)
2. Deduplicate similar events (keep the most complete version)
3. Focus on events that photographers can actually attend
4. Return ONLY the top 15 most promising events

For each event, extract ALL available information:
- title: Descriptive title that captures what makes this event interesting
- date: MANDATORY specific date (YYYY-MM-DD format)
- time: Include if mentioned (e.g., "7:30 PM", "morning", "all day") or make reasonable inference (e.g., "evening" for concerts)
- location: Specific venue or address (MANDATORY)
- description: What makes this event visually interesting or newsworthy
- organizer: Who is organizing (if mentioned)
- url: Source URL where you found this information (MANDATORY)

GUIDELINES:
- MUST have specific date and location
- Time is valuable but not required - include when available or inferable
- Always include a meaningful description explaining the event's appeal
- Always include the source URL for verification
- Deduplicate: combine information from multiple sources about the same event
- Skip events that already happened or have no specific date
- LIMIT: Return maximum 15 events"""
        
        # Format evidence for LLM
        evidence_text = self._format_evidence_for_llm(evidence)
        
        user_prompt = f"""Extract unique events from these search results:

{evidence_text}

Return the 15 BEST events prioritizing:
1. Events with specific dates and locations (required)
2. High photographic/visual potential
3. Strong news value or cultural significance
4. Events matching user interests

For each event:
- Extract time if mentioned, otherwise provide reasonable estimate ("morning", "evening", "all day")
- Write a brief description explaining WHY this event is interesting
- Include the source URL where you found the most complete information

Return JSON:
{{
    "events": [
        {{
            "title": "Descriptive event title",
            "date": "YYYY-MM-DD",  // REQUIRED
            "time": "Time if known OR reasonable estimate",
            "location": "Specific venue/address",  // REQUIRED
            "description": "What makes this visually interesting",
            "organizer": "Organization name if mentioned",
            "access_req": "Public/Press/Ticketed if mentioned",
            "url": "https://source-url.com"  // REQUIRED
        }}
    ]
}}

Maximum 15 events. Focus on quality over quantity."""
        
        # Get LLM response
        response = self.llm_client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2500,  # Sufficient for 15 events
            temperature=1.0
        )
        
        # Update cost tracking
        self.total_cost += response["cost"]
        
        return response["parsed_content"]["events"]
    
    def _make_gate_decision(
        self, 
        events: List[Dict[str, Any]], 
        profile: Dict[str, Any],
        leads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make gate decision on whether events meet quality threshold.
        
        Args:
            events: Extracted unique events
            profile: User profile with interests
            leads: Original leads from Researcher
            
        Returns:
            Decision dict with 'decision', 'events', and 'feedback'
        """
        if not events:
            return {
                "decision": "RETRY",
                "events": [],
                "feedback": "No events found. Need more specific search queries or different event types."
            }
        
        # Build prompt for gate decision
        interests = profile.get("interests", ["news", "events"])
        
        system_prompt = f"""You are a photo editor making decisions about event coverage.

User interests: {', '.join(interests)}

Your job is to evaluate if we have at least 5 HIGH-QUALITY events worth covering.

High-quality events must have:
1. Specific date (exact YYYY-MM-DD)
2. Specific location (venue or address)
3. Clear photographic potential
4. Relevance to user interests

Time information is valuable but not required - many legitimate events don't announce specific times until closer to the date.

Make a gate decision:
- APPROVE: If you have 5+ high-quality events
- RETRY: If quality or quantity is insufficient"""
        
        # Format events for evaluation
        events_text = "\n".join([
            f"{i+1}. {e['title']} - {e.get('date', 'No date')} at {e.get('location', 'No location')}"
            for i, e in enumerate(events)
        ])
        
        user_prompt = f"""Evaluate these {len(events)} events:

{events_text}

If APPROVE: Return the top 10 events from those provided, scored 0-100 based on:
- Photographic potential (visual interest, action, emotion)
- Newsworthiness (timeliness, relevance, impact)
- Specificity (clear time, location, access info)

If RETRY: Explain what's missing and suggest what to search for.

Return JSON:
{{
    "decision": "APPROVE or RETRY",
    "events": [  // if APPROVE
        {{
            "title": "Event title",
            "score": 85,
            ...all original fields...
        }}
    ],
    "feedback": "Explanation if RETRY"
}}"""
        
        # Get LLM response
        response = self.llm_client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
            temperature=1.0
        )
        
        # Update cost tracking
        self.total_cost += response["cost"]
        
        result = response["parsed_content"]
        
        # If approved, sort by score and take top 10
        if result["decision"] == "APPROVE" and result.get("events"):
            result["events"] = sorted(
                result["events"], 
                key=lambda x: x.get("score", 0), 
                reverse=True
            )[:10]
        
        return result
    
    def _format_evidence_for_llm(self, evidence: List[Dict[str, Any]]) -> str:
        """Format evidence for LLM processing.
        
        Args:
            evidence: Evidence from Fact-Checker
            
        Returns:
            Formatted text
        """
        formatted = []
        
        for i, item in enumerate(evidence):
            lead = item.get("lead", {})
            results = item.get("results", [])
            
            formatted.append(f"\n=== Lead {i+1}: {lead.get('description', 'Unknown')} ===")
            
            for j, result in enumerate(results[:5]):  # Limit to top 5 results per lead
                formatted.append(f"\nSource {j+1}: {result.get('url', '')}")
                formatted.append(f"Title: {result.get('title', '')}")
                formatted.append(f"Content: {result.get('content', '')[:500]}...")  # Truncate long content
            
            if item.get("answer"):
                formatted.append(f"\nSummary: {item['answer']}")
        
        return "\n".join(formatted)
    
    def _format_final_output(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format events for final output.
        
        Args:
            events: Approved events with scores
            
        Returns:
            Formatted events
        """
        formatted = []
        
        for event in events:
            # Ensure all required fields
            # Skip events without dates
            if not event.get("date") or event.get("date") == "null":
                continue
                
            formatted_event = {
                "title": event.get("title", "Untitled Event"),
                "date": event.get("date"),
                "time": event.get("time"),
                "location": event.get("location", "Location TBD"),
                "description": event.get("description", ""),
                "organizer": event.get("organizer"),
                "url": event.get("url", ""),
                "score": event.get("score", 0),
                "interesting": event.get("score", 0) >= 70  # Mark as interesting if score >= 70
            }
            formatted.append(formatted_event)
        
        return formatted
    
    def validate_output(self, state: Dict[str, Any]) -> bool:
        """Validate publisher output.
        
        Args:
            state: State with events or feedback
            
        Returns:
            True if valid
        """
        if "gate_decision" not in state:
            logger.error("No gate decision in state")
            return False
        
        decision = state["gate_decision"]
        
        if decision == "APPROVE":
            if "events" not in state or not state["events"]:
                logger.error("APPROVE decision but no events")
                return False
            
            # Check event structure
            for event in state["events"]:
                required = ["title", "location"]
                if not all(field in event for field in required):
                    logger.error(f"Event missing required fields: {event}")
                    return False
        
        elif decision == "RETRY":
            if "feedback" not in state:
                logger.error("RETRY decision but no feedback")
                return False
        
        logger.info(f"Validated publisher output: {decision}")
        return True