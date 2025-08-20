"""Editor Agent v0.4.0 - LLM-based profile builder and feedback handler."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class EditorV4(BaseAgent):
    """Editor that uses LLM to create profiles and handle feedback."""
    
    def __init__(self):
        """Initialize Editor v0.4.0."""
        super().__init__(name="editor_v4", use_cache=False)  # No caching for Editor
        self.llm_client = get_llm_client(model="gpt-4.1-mini", temperature=1.0)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input and/or Publisher feedback to create profile.
        
        Args:
            state: Workflow state with user input and optional feedback
            
        Returns:
            Updated state with profile and guidance
        """
        try:
            # Build profile with LLM (handles both initial and retry)
            logger.info("Building profile with LLM...")
            profile = self._build_profile_with_llm(state)
            
            # Update state
            state["profile"] = profile
            state["location"] = profile["location"]
            state["time_frame"] = profile["time_frame"]
            
            # Track metrics
            state["editor_metrics"] = {
                "iteration": profile["iteration"],
                "llm_cost": self.total_cost
            }
            
            # Determine if we should continue with retries
            if profile["iteration"] > 3:
                state["should_retry"] = False
                state["max_retries_reached"] = True
                logger.warning(f"Reached maximum iterations ({profile['iteration']})")
            else:
                state["should_retry"] = True
            
            logger.info(f"Created profile for iteration {profile['iteration']}")
            return state
            
        except Exception as e:
            logger.error(f"Error in Editor: {e}")
            self.errors.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            
            # Return minimal profile on error
            state["profile"] = {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["events"],
                "iteration": 1,
                "researcher_guidance": "Generate diverse newsworthy events"
            }
            state["editor_metrics"] = {"error": str(e)}
            return state
    
    def _build_profile_with_llm(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to build comprehensive profile and guidance.
        
        Args:
            state: Current state with user input and optional feedback
            
        Returns:
            Profile dict with guidance
        """
        # Prepare context for LLM
        context = self._format_context_for_llm(state)
        
        # System prompt
        system_prompt = """You are an expert news editor planning event coverage for photojournalists.

Your job is to:
1. Understand what the user wants to find
2. If this is a retry, understand what went wrong and adjust
3. Create a profile that helps find the right events
4. Write specific guidance for the Researcher to generate better event leads

Consider:
- Event types that match user interests
- Specific keywords and themes to focus on
- What to avoid based on any feedback
- Seasonal and current events context"""
        
        # User prompt with context
        user_prompt = f"""{context}

Create a comprehensive profile for event discovery.

Return JSON with:
{{
    "location": "Event location",
    "time_frame": "Time period for events",
    "interests": ["list", "of", "interest", "areas"],
    "iteration": 1,  // or higher if retry
    "focus_event_types": ["specific", "event", "types", "to", "prioritize"],
    "avoid_event_types": ["event", "types", "to", "skip"],
    "key_organizations": ["organizations", "to", "look", "for"],
    "researcher_guidance": "Specific instructions for the Researcher on what event leads to generate",
    "search_themes": ["themes", "and", "topics", "to", "explore"]
}}"""
        
        # Get LLM response
        response = self.llm_client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=1.0
        )
        
        # Update cost tracking
        self.total_cost += response["cost"]
        
        profile = response["parsed_content"]
        
        # Ensure required fields
        profile.setdefault("location", "New York City")
        profile.setdefault("time_frame", "this week")
        profile.setdefault("interests", ["events"])
        profile.setdefault("iteration", 1)
        profile.setdefault("researcher_guidance", "Generate diverse newsworthy events")
        
        return profile
    
    def _format_context_for_llm(self, state: Dict[str, Any]) -> str:
        """Format state information as context for LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add user input
        user_input = state.get("user_input", {})
        if isinstance(user_input, str):
            context_parts.append(f"User request: {user_input}")
        else:
            location = user_input.get("location", "New York City")
            time_frame = user_input.get("time_frame", "this week")
            interests = user_input.get("interests", [])
            
            context_parts.append(f"User request: Find events in {location} for {time_frame}")
            if interests:
                context_parts.append(f"User interests: {', '.join(interests)}")
        
        # Add iteration info if retry
        current_profile = state.get("profile", {})
        iteration = current_profile.get("iteration", 0)
        
        if iteration > 0:
            context_parts.append(f"\nThis is iteration {iteration + 1} (retry)")
        
        # Add Publisher feedback if present
        if state.get("gate_decision") == "RETRY" and state.get("feedback"):
            context_parts.append(f"\nPublisher feedback from previous attempt:")
            context_parts.append(f"{state['feedback']}")
            
            # Add what was tried before
            if current_profile.get("researcher_guidance"):
                context_parts.append(f"\nPrevious guidance was: {current_profile['researcher_guidance']}")
        
        # Add previous leads summary if available
        if state.get("leads"):
            lead_types = {}
            for lead in state["leads"][:10]:  # Sample first 10
                lead_type = lead.get("type", "unknown")
                lead_types[lead_type] = lead_types.get(lead_type, 0) + 1
            
            context_parts.append(f"\nPrevious attempt generated: {lead_types}")
        
        # Add found events summary if available
        if state.get("events"):
            context_parts.append(f"\nEvents found but rejected: {len(state['events'])}")
        
        return "\n".join(context_parts)
    
    def validate_output(self, state: Dict[str, Any]) -> bool:
        """Validate Editor output.
        
        Args:
            state: State with profile
            
        Returns:
            True if valid
        """
        if "profile" not in state:
            logger.error("No profile in state")
            return False
        
        profile = state["profile"]
        required_fields = ["location", "time_frame", "interests", "researcher_guidance"]
        
        for field in required_fields:
            if field not in profile:
                logger.error(f"Profile missing required field: {field}")
                return False
        
        logger.info("Validated Editor output")
        return True